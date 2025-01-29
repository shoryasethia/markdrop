# To ignore warnings
from ignore_warnings import *

from utils import extract_images, make_markdown, extract_tables_from_pdf
from models.img_descriptions import generate_descriptions
from models.setup_keys import setup_keys
from helper import analyze_pdf_images

### PDF Conversion

source_pdf = 'url/or/path/to/pdf/file'    # Replace with your local PDF file path or a URL
output_dir = 'data/output'                # Replace it with desired output directory's path

make_markdown(source_pdf, output_dir)
extract_images(source_pdf, output_dir)
extract_tables_from_pdf(source_pdf, output_dir=output_dir)


### Analyze different types of image references in a PDF

pdf_path = 'path/to/pdf/file'             # Replace with your local PDF file pathL
output_dir = "output/data/image_xref"     # Replace it with desired output directory's path

analyze_pdf_images(pdf_path, output_dir, verbose=True, save_images=True)

### API Key Setup
### If using 'openai' or 'gemini' as llm_client in the generate_descriptions function, you need to set up the API keys first.

setup_keys(key = 'google')  # or setup_keys(key = 'openai'), if using models = ['openai'] in the generate_descriptions function





### Image Descriptions Generation

prompt = "Give textual highly detailed descriptions from this image ONLY, nothing else." # Replace it with your desired prompt
input_path = 'path/to/img_file/or/dir'    # Replace it with the path to the images dir or image file
output_dir = 'data/output'                # Replace it with the desired output directory's path
models = ['gemini']        # Replace it with the desired models from ['qwen', 'gemini', 'openai', 'llama-vision', 'molmo', 'pixtral'] only

generate_descriptions(input_path = input_path, output_dir = output_dir, prompt = prompt, llm_client = models)
