from .ignore_warnings import *
import os
import sys
import fitz
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry #type: ignore

import tempfile
from urllib.parse import urlparse
from docling.document_converter import DocumentConverter

from transformers import TableTransformerForObjectDetection, DetrImageProcessor
from PIL import Image
import torch

def create_robust_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504, 104]
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def download_pdf(url, output_dir=None):
    try:
        print(f"Attempting to download PDF from: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        session = create_robust_session()
        response = session.get(url, headers=headers, stream=True, allow_redirects=True)
        response.raise_for_status()
        
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

        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded_size = 0

        print(f"Saving PDF to: {filepath}")
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"Download progress: {progress:.1f}%", end='\r')

        print("\nDownload complete. Verifying PDF...")

        try:
            with fitz.open(filepath) as doc:
                _ = doc[0]
                page_count = len(doc)
                print(f"Valid PDF verified: {page_count} pages")
        except Exception as e:
            os.remove(filepath)
            raise ValueError(f"Downloaded file is not a valid PDF: {str(e)}")

        return filepath

    except Exception as e:
        if isinstance(e, requests.exceptions.RequestException):
            print(f"Retrying download due to error: {str(e)}")
            # Second attempt with different headers
            try:
                headers = {
                    'User-Agent': 'curl/7.64.1',
                    'Accept': 'application/pdf'
                }
                session = create_robust_session()
                response = session.get(url, headers=headers, stream=True)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return filepath
            except Exception as retry_error:
                raise Exception(f"Error downloading PDF after retry: {str(retry_error)}")
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
    Extract all images from PDF using xref IDs, handling multiple instances and formats.
    """
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            pdf_path = download_pdf(source, download_dir)
        else:
            pdf_path = source

        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        with fitz.open(pdf_path) as pdf_reader:
            images = []
            xref_dict = {}  # Track unique images by their content hash
            
            for page_number in range(pdf_reader.page_count):
                page = pdf_reader[page_number]
                
                # Get both referenced images and images from form XObjects
                img_list = page.get_images()
                
                for img in img_list:
                    xref = img[0]
                    
                    try:
                        image_data = recoverpix(pdf_reader, img)
                        if not image_data:
                            continue
                            
                        imgdata = image_data["image"]
                        content_hash = hash(imgdata)
                        
                        # Only save if we haven't seen this exact image before
                        if content_hash not in xref_dict:
                            xref_dict[content_hash] = xref
                            imgfile = os.path.join(images_dir, f"img_{xref}.{image_data['ext']}")
                            
                            with open(imgfile, "wb") as fout:
                                fout.write(imgdata)
                            
                            images.append(imgfile)
                            
                            if verbose:
                                print(f"Extracted image {len(images)} (xref: {xref}) from page {page_number + 1}")
                    
                    except Exception as e:
                        if verbose:
                            print(f"Failed to extract image with xref {xref}: {str(e)}")
                        continue

            if verbose:
                print(f"Successfully extracted {len(images)} unique images to {images_dir}")

            return images

    except Exception as e:
        print(f"An error occurred while extracting images: {e}")
        raise
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose)

def make_markdown(source, output_dir, verbose=False):
    """
    Converts a PDF to markdown with proper encoding handling
    """
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            pdf_path = download_pdf(source, download_dir)
        else:
            pdf_path = source

        output_dir = os.path.join(output_dir, "markdown")
        os.makedirs(output_dir, exist_ok=True)

        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        result_str = result.document.export_to_markdown()

        output_txt_path = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '.txt'))
        
        # Handle encoding properly
        with open(output_txt_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(result_str)
        
        if verbose:
            print(f"Markdown file saved as {output_txt_path}")

    except UnicodeEncodeError as e:
        print(f"Handling Unicode error: {str(e)}")
        # Fallback encoding handling
        with open(output_txt_path, 'w', encoding='ascii', errors='ignore') as f:
            f.write(result_str)
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