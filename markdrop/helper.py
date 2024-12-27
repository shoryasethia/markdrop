import pymupdf as fitz
import os
import json
from collections import defaultdict
from typing import Dict, Optional
from datetime import datetime

def analyze_pdf_images_main(source: str, output_dir: str, verbose: bool = False, save_images: bool = False) -> Dict[str, dict]:
    """
    Analyze different types of image references in a PDF and save results
    
    Args:
        source: Local file path or URL to PDF
        output_dir: Directory for saving analysis results and extracted images
        verbose: Print detailed information
        save_images: If True, saves extracted images to output_dir
        
    Returns:
        Dictionary containing analysis results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    download_dir = None
    try:
        if source.startswith(('http://', 'https://')):
            download_dir = os.path.join(output_dir, "downloaded_pdfs")
            from .utils import download_pdf, cleanup_download_dir
            pdf_path = download_pdf(source, download_dir)
        else:
            pdf_path = source

        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with fitz.open(pdf_path) as doc:
            embedded_images = {}
            markdown_refs = defaultdict(lambda: {"count": 0, "xrefs": set()})
            
            # Create images directory if saving images
            if save_images:
                images_dir = os.path.join(output_dir, f"{pdf_name}_images_{timestamp}")
                os.makedirs(images_dir, exist_ok=True)
            
            for page_num, page in enumerate(doc, 1):
                # Analyze embedded images
                for img_idx, img in enumerate(page.get_images()):
                    xref = img[0]
                    if xref not in embedded_images:
                        embedded_images[xref] = {
                            "width": img[2],
                            "height": img[3],
                            "bpc": img[4],
                            "colorspace": img[5],
                            "compression": img[6],
                            "first_seen_page": page_num
                        }
                        
                        # Save image if requested
                        if save_images:
                            try:
                                pix = fitz.Pixmap(doc, xref)
                                img_path = os.path.join(images_dir, f"page{page_num}_img{img_idx}_{xref}")
                                
                                if pix.n >= 5:  # CMYK: convert to RGB first
                                    pix = fitz.Pixmap(fitz.csRGB, pix)
                                    
                                if pix.alpha:  # Remove alpha channel if present
                                    pix = fitz.Pixmap(pix, 0)
                                
                                # Save as PNG
                                pix.save(f"{img_path}.png")
                                embedded_images[xref]["saved_path"] = f"{img_path}.png"
                                
                            except Exception as e:
                                if verbose:
                                    print(f"Error saving image {xref}: {e}")
                
                # Analyze markdown/external references
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block.get("type") == 1:
                        markdown_refs[page_num]["count"] += 1
                        if "xref" in block:
                            markdown_refs[page_num]["xrefs"].add(block["xref"])
            
            # Convert sets to lists for JSON serialization
            markdown_refs = {k: {"count": v["count"], "xrefs": list(v["xrefs"])} 
                           for k, v in markdown_refs.items()}
            
            pages_with_embedded = {props["first_seen_page"] for props in embedded_images.values()}
            pages_with_refs = set(markdown_refs.keys())
            
            summary = {
                "total_embedded": len(embedded_images),
                "total_markdown_refs": sum(ref["count"] for ref in markdown_refs.values()),
                "unique_images": len({img["compression"] for img in embedded_images.values()}),
                "pages_with_images": len(pages_with_embedded | pages_with_refs)
            }
            
            result = {
                "pdf_name": pdf_name,
                "analysis_timestamp": timestamp,
                "embedded_images": embedded_images,
                "markdown_refs": markdown_refs,
                "summary": summary
            }
            
            # Save analysis results as JSON
            result_path = os.path.join(output_dir, f"{pdf_name}_analysis_{timestamp}.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            if verbose:
                print(f"\nPDF Analysis Results for {pdf_name}:")
                print(f"Total embedded images: {summary['total_embedded']}")
                print(f"Total markdown references: {summary['total_markdown_refs']}")
                print(f"Pages containing images: {summary['pages_with_images']}")
                print(f"\nResults saved to: {result_path}")
                if save_images:
                    print(f"Images saved to: {images_dir}")
                
            return result

    except Exception as e:
        print(f"Error analyzing PDF images: {e}")
        raise
    finally:
        if download_dir:
            cleanup_download_dir(download_dir, verbose)

def analyze_pdf_images(source: str, output_dir: str, verbose: bool = True, save_images: bool = True):
    
    try:
        result = analyze_pdf_images_main(
            source=source,
            output_dir=output_dir,
        )
    except Exception as e:
        print(f"Error running analysis: {e}")
