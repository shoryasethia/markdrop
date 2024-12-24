import os
import sys
import fitz
from docling.document_converter import DocumentConverter

from transformers import TableTransformerForObjectDetection, DetrImageProcessor
from PIL import Image
import torch

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
    
    Args:
    - source (str): Path to the input PDF.
    - output_dir (str): Directory where the images will be saved.
    
    Returns:
    - list of image file paths
    """
    try:
        # Check if output directory exists, if not, create it
        images_dir = os.path.join(output_dir, "images")
        if not os.path.isdir(images_dir):
            os.makedirs(images_dir)  # Create images directory

        # Open PDF and extract images
        with fitz.open(source) as pdf_reader:
            images = []
            xreflist = []  # Keep track of xref IDs to avoid duplicates
            for page_number in range(pdf_reader.page_count):
                img_list = pdf_reader.get_page_images(page_number)
                for img in img_list:
                    xref = img[0]  # xref of the image
                    if xref in xreflist:
                        continue  # Skip if image already processed
                    xreflist.append(xref)

                    # Extract the image based on xref ID
                    image_data = recoverpix(pdf_reader, img)
                    imgdata = image_data["image"]
                    imgfile = os.path.join(images_dir, f"img_{xref}.{image_data['ext']}")

                    # Save image to disk
                    with open(imgfile, "wb") as fout:
                        fout.write(imgdata)

                    images.append(imgfile)  # Store the image path
            
            if verbose:
                print(f"All images saved in {images_dir}.")
            return images

    except Exception as e:
        print(f"An error occurred while extracting images: {e}")
        sys.exit(1)  # Exit with error code 1

def make_markdown(source, output_dir, verbose=False):
    """
    Converts a PDF to markdown (.txt) format and saves it in the specified output directory.
    
    Args:
    - source (str): Path to the input PDF.
    - output_dir (str): Directory where the .txt markdown file will be saved.
    
    Raises:
    - Exception: For general error handling.
    """
    try:
        # Check if output directory exists, if not, create it
        output_dir = os.path.join(output_dir, "markdown")
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        # Convert the PDF to markdown using DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(source)
        result_str = result.document.export_to_markdown()

        # Save markdown to a .txt file
        output_txt_path = os.path.join(output_dir, os.path.basename(source).replace('.pdf', '.txt'))
        with open(output_txt_path, 'w') as f:
            f.write(result_str)
        
        if verbose:
            print(f"Markdown file saved as {output_txt_path}")

    except Exception as e:
        print(f"An error occurred while converting PDF to markdown: {e}")
        sys.exit(1)  # Exit with error code 1

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
def extract_tables_from_pdf(pdf_path, start_page=0, end_page=None, threshold=0.8, 
                            output_dir="data/output", padding_top_bottom=50, 
                            padding_left_right=20, delete_cache=True, verbose=False):
    # Create output directories if they don't exist
    images_dir = os.path.join(output_dir, "images")
    table_images_dir = os.path.join(output_dir, "table_images")

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(table_images_dir, exist_ok=True)

    # Clear the output directory if delete_cache is True
    if delete_cache:
        for filename in os.listdir(table_images_dir):
            file_path = os.path.join(table_images_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)  # Remove directory if needed
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

    # Get images only for the specified page range
    images = pdf_to_images(pdf_path, start_page, end_page)
    table_results = detect_tables(images)
    
    tot_tables = 0  # Track the total number of detected tables
    
    # Print or process the detected tables
    for page_num, results in enumerate(table_results, start=start_page):
        for result in results:
            for box, score, label in zip(result["boxes"], result["scores"], result["labels"]):
                if score.item() >= threshold:
                    tot_tables += 1  # Increment the table counter
                    
                    # Convert box coordinates to integers
                    box = box.int().tolist()  # box is a tensor; convert to list
                    x0, y0, x1, y1 = box
                    # Add padding to the coordinates
                    x0 = max(0, x0 - padding_left_right)  # Ensure x0 doesn't go below 0
                    y0 = max(0, y0 - padding_top_bottom)   # Ensure y0 doesn't go below 0
                    x1 = min(images[page_num - start_page].width, x1 + padding_left_right)  # Ensure x1 doesn't go beyond image width
                    y1 = min(images[page_num - start_page].height, y1 + padding_top_bottom) # Ensure y1 doesn't go beyond image height
                    # Crop the image using the bounding box coordinates with padding
                    cropped_image = images[page_num - start_page].crop((x0, y0, x1, y1))
                    # Save the cropped image
                    table_image_path = os.path.join(table_images_dir, f"table_page_{page_num + 1}_box_{len(os.listdir(table_images_dir)) + 1}.png")
                    cropped_image.save(table_image_path)
                    if verbose:
                        print(f"Detected table with score {score.item():.3f} at {box}. Saved as {table_image_path}")
    # Final summary of extracted tables
    if verbose:
        print(f"Extraction complete: {tot_tables} tables detected and saved in {table_images_dir}.")

