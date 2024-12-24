# To ignore warnings
from ignore_warnings import *

# Import the necessary functions and libraries
from utils import extract_images, make_markdown, extract_tables_from_pdf
from tqdm import tqdm


source_pdf = 'path_or_link_to_pdf'  # Replace with your local PDF file path or a URL
output_dir = 'data/output'          # Replace it with desired output directory's path

print("Converting PDF to markdown...")
with tqdm(total=1, desc="Markdown Conversion", unit="step") as pbar:
    make_markdown(source_pdf, output_dir)
    pbar.update(1)

print("Extracting images from PDF...")
with tqdm(total=1, desc="Image Extraction", unit="step") as pbar:
    extract_images(source_pdf, output_dir)
    pbar.update(1)

print("Extracting tables from PDF...")
with tqdm(total=1, desc="Table Extraction", unit="step") as pbar:
    extract_tables_from_pdf(source_pdf, output_dir=output_dir)
    pbar.update(1)
