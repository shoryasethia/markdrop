import os
import sys
import fitz
import requests
import tempfile
from urllib.parse import urlparse
from docling.document_converter import DocumentConverter

from transformers import TableTransformerForObjectDetection, DetrImageProcessor
from PIL import Image
import torch

def download_pdf(url, output_dir=None):
    """
    Download a PDF file from any URL and save it locally.
    
    Args:
    - url (str): URL of the PDF file
    - output_dir (str, optional): Directory to save the downloaded PDF
    
    Returns:
    - str: Path to the downloaded PDF file
    """
    try:
        print(f"Attempting to download PDF from: {url}")
        
        # Set up headers to mimic a browser for better compatibility
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Follow redirects to get the final URL
        response = requests.get(url, headers=headers, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # If output_dir is provided, save there; otherwise use a temp file
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.basename(urlparse(response.url).path) or 'downloaded.pdf'
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            filepath = os.path.join(output_dir, filename)
        else:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            filepath = temp.name
            temp.close()

        # Download and save the file
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded_size = 0

        print(f"Saving PDF to: {filepath}")
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:  # Only show progress if we know the total size
                        progress = (downloaded_size / total_size) * 100
                        print(f"Download progress: {progress:.1f}%", end='\r')

        print("\nDownload complete. Verifying PDF...")

        # Verify the downloaded file is a valid PDF
        try:
            with fitz.open(filepath) as doc:
                # Try to access the first page to verify PDF is valid
                _ = doc[0]
                page_count = len(doc)
                print(f"Valid PDF verified: {page_count} pages")
        except Exception as e:
            os.remove(filepath)
            raise ValueError(f"Downloaded file is not a valid PDF: {str(e)}")

        return filepath

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading PDF: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing PDF download: {str(e)}")

def cleanup_download_dir(download_dir, verbose=False):
    """
    Clean up the downloads directory and all its contents.
    
    Args:
    - download_dir (str): Path to the downloads directory
    - verbose (bool): Whether to print progress messages
    """
    try:
        if os.path.exists(download_dir):
            # Remove all files in the directory
            for filename in os.listdir(download_dir):
                filepath = os.path.join(download_dir, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting file {filepath}: {e}")
            
            # Remove the directory itself
            os.rmdir(download_dir)
            if verbose:
                print(f"Cleaned up downloads directory: {download_dir}")
    except Exception as e:
        print(f"Error cleaning up downloads directory: {e}")

def recoverpix(doc, item):
    """
    Extract image based on xref ID.
    """
    xref = item[0]  # xref of the PDF image
    smask = item[1]  # xref of its /SMask (mask for transparency)

    if smask > 0:
        pix0 = fitz.Pixmap(doc.extract_image(xref)["image"])
        if pix0.alpha:  # Remove alpha channel if present
            pix0 = fitz.Pixmap(pix0, 0)  # Remove alpha channel
        mask = fitz.Pixmap(doc.extract_image(smask)["image"])
        try:
            pix = fitz.Pixmap(pix0, mask)  # Combine the image with its mask
        except:  # Fallback if combining fails
            pix = fitz.Pixmap(doc.extract_image(xref)["image"])

        if pix0.n > 3:
            ext = "pam"  # PAM format for images with more than 3 channels
        else:
            ext = "png"  # PNG format for normal images

        return {"ext": ext, "image": pix.tobytes(ext)}

    if "/ColorSpace" in doc.xref_object(xref, compressed=True):
        pix = fitz.Pixmap(doc, xref)
        pix = fitz.Pixmap(fitz.csRGB, pix)  # Convert to RGB if not already
        return {"ext": "png", "image": pix.tobytes("png")}

    return doc.extract_image(xref)  # Extract image without additional processing

def extract_images(source, output_dir, verbose=False):
    """
    Extract images based on xref ID from the PDF and save them to the specified directory.
    """
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            pdf_path = download_pdf(source, download_dir)
            if verbose:
                print(f"Successfully downloaded PDF to: {pdf_path}")
        else:
            pdf_path = source
            if verbose:
                print(f"Using local PDF file: {pdf_path}")

        images_dir = os.path.join(output_dir, "images")
        if not os.path.isdir(images_dir):
            os.makedirs(images_dir)

        with fitz.open(pdf_path) as pdf_reader:
            images = []
            xreflist = []
            for page_number in range(pdf_reader.page_count):
                img_list = pdf_reader.get_page_images(page_number)
                for img in img_list:
                    xref = img[0]
                    if xref in xreflist:
                        continue
                    xreflist.append(xref)

                    image_data = recoverpix(pdf_reader, img)
                    imgdata = image_data["image"]
                    imgfile = os.path.join(images_dir, f"img_{xref}.{image_data['ext']}")

                    with open(imgfile, "wb") as fout:
                        fout.write(imgdata)

                    images.append(imgfile)
            
            if verbose:
                print(f"All images saved in {images_dir}.")

            return images

    except Exception as e:
        print(f"An error occurred while extracting images: {e}")
        sys.exit(1)
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose)


def make_markdown(source, output_dir, verbose=False):
    """
    Converts a PDF to markdown (.txt) format and saves it in the specified output directory.
    """
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            pdf_path = download_pdf(source, download_dir)
            if verbose:
                print(f"Successfully downloaded PDF to: {pdf_path}")
        else:
            pdf_path = source
            if verbose:
                print(f"Using local PDF file: {pdf_path}")

        output_dir = os.path.join(output_dir, "markdown")
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        result_str = result.document.export_to_markdown()

        output_txt_path = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.txt'))
        with open(output_txt_path, 'w') as f:
            f.write(result_str)
        
        if verbose:
            print(f"Markdown file saved as {output_txt_path}")

    except Exception as e:
        print(f"An error occurred while converting PDF to markdown: {e}")
        sys.exit(1)
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose)


def load_tatr():
    # Load the model and processor
    model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
    processor = DetrImageProcessor.from_pretrained("microsoft/table-transformer-detection")
    return model, processor

model, processor = load_tatr()

# Function to convert PDF pages to images
def pdf_to_images(pdf_path, start_page=0, end_page=None):
    doc = fitz.open(pdf_path)
    images = []
    
    # Handle the case where end_page is not provided or exceeds the total number of pages
    end_page = min(end_page if end_page is not None else len(doc), len(doc))

    for page_num in range(start_page, end_page):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)  # Adjust dpi for higher/lower resolution
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    
    return images

# Function to detect tables in images
def detect_tables(images):
    table_results = []
    for image in images:
        # Preprocess the image
        inputs = processor(images=image, return_tensors="pt")

        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)

        # Post-process the outputs
        target_sizes = torch.tensor([image.size[::-1]])
        results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)

        # Store results
        table_results.append(results)
    return table_results

# Function to extract and save table images from a specific page range in the PDF
def extract_tables_from_pdf(source, start_page=0, end_page=None, threshold=0.8, 
                          output_dir="data/output", padding_top_bottom=50, 
                          padding_left_right=20, delete_cache=True, verbose=False):
    """
    Extract tables from a PDF file or URL.
    """
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            pdf_path = download_pdf(source, download_dir)
            if verbose:
                print(f"Successfully downloaded PDF to: {pdf_path}")
        else:
            pdf_path = source
            if verbose:
                print(f"Using local PDF file: {pdf_path}")
            
        images_dir = os.path.join(output_dir, "images")
        table_images_dir = os.path.join(output_dir, "table_images")
        
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(table_images_dir, exist_ok=True)
        
        if delete_cache:
            for filename in os.listdir(table_images_dir):
                file_path = os.path.join(table_images_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        os.rmdir(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        if verbose:
            print("Starting table extraction...")
            
        images = pdf_to_images(pdf_path, start_page, end_page)
        if verbose:
            print(f"Converted {len(images)} pages to images")
            
        table_results = detect_tables(images)
        
        tot_tables = 0
        
        for page_num, results in enumerate(table_results, start=start_page):
            for result in results:
                for box, score, label in zip(result["boxes"], result["scores"], result["labels"]):
                    if score.item() >= threshold:
                        tot_tables += 1
                        
                        box = box.int().tolist()
                        x0, y0, x1, y1 = box
                        x0 = max(0, x0 - padding_left_right)
                        y0 = max(0, y0 - padding_top_bottom)
                        x1 = min(images[page_num - start_page].width, x1 + padding_left_right)
                        y1 = min(images[page_num - start_page].height, y1 + padding_top_bottom)
                        
                        cropped_image = images[page_num - start_page].crop((x0, y0, x1, y1))
                        table_image_path = os.path.join(table_images_dir, f"table_page_{page_num + 1}_box_{len(os.listdir(table_images_dir)) + 1}.png")
                        cropped_image.save(table_image_path)
                        
                        if verbose:
                            print(f"Detected table with score {score.item():.3f} on page {page_num + 1}")
        
        if verbose:
            print(f"Extraction complete: {tot_tables} tables detected and saved in {table_images_dir}")

    except Exception as e:
        print(f"An error occurred while extracting tables: {e}")
        sys.exit(1)
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose)