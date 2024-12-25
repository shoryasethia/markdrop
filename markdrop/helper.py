import fitz
import os
from utils import download_pdf, cleanup_download_dir

pdf_path = 'url/or/path/to/pdf/file'
output_dir = 'data/output'

def analyze_pdf_images(source, output_dir, verbose=False):
    """
    Analyze different types of image references in a PDF from local file or URL
    
    Args:
        source: Local file path or URL to PDF
        output_dir: Directory for temporary files
        verbose: Print detailed information
    """
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            pdf_path = download_pdf(source, download_dir)
        else:
            pdf_path = source

        with fitz.open(pdf_path) as doc:
            embedded_images = set()
            markdown_image_refs = 0
            
            for page in doc:
                for img in page.get_images():
                    embedded_images.add(img[0])
                
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block.get("type") == 1:
                        markdown_image_refs += 1
            
            return len(embedded_images), markdown_image_refs

    except Exception as e:
        print(f"Error analyzing PDF images: {e}")
        raise
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose)

embedded_count, ref_count = analyze_pdf_images(pdf_path, output_dir)
print(f"Embedded: {embedded_count}, References: {ref_count}")           
