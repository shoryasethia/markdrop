from pathlib import Path
from .api_setup import setup_apikeys
from .process import markdrop, MarkDropConfig, add_downloadable_tables, logging
from .parse import process_markdown, ProcessorConfig, AIProvider, logger

# Use with default configuration
input_doc_path = "path/to/input.pdf"
output_dir = Path('output_directory')

########### <Default configuration> ###########
config = MarkDropConfig(
    image_resolution_scale=2,
    download_button_color='#444444',
    log_level=logging.INFO
)
########### </Default configuration> ###########

# Get the markdrop output
html_path = markdrop(input_doc_path, output_dir, config)
downloadable_html = add_downloadable_tables(html_path, config)


#-----------------------------------------------------------------------------#

setup_apikeys(key = 'gemini')      # setup_keys(key = 'openai')

# Construct the markdown path based on input_doc_path
input_doc_stem = Path(input_doc_path).stem
markdown_path = output_dir / f"{input_doc_stem}-markdroped.md"

########### <Default prompts> ###########
DEFAULT_IMAGE_PROMPT = """
Provide a detailed, contextually rich description of this image. Include visual details, 
context, data, and any relevant information that would help someone understand what this image 
conveys without seeing it. Make it descriptive enough to serve as a replacement for the image.
"""

DEFAULT_TABLE_PROMPT = """
Analyze this markdown table and provide a detailed description of its contents.
Include key insights, patterns, and important details. Make the summary
comprehensive enough to replace the original table.

Table:
"""
########### </Default prompts> ###########

config = ProcessorConfig(
    input_path=markdown_path,  # Using the automatically constructed markdown path
    output_dir=output_dir,     # Reusing the same output directory
    ai_provider=AIProvider.GEMINI,
    remove_images=False,
    remove_tables=False,
    table_descriptions=True,
    image_descriptions=True,
    max_retries=3,
    retry_delay=2,
    gemini_model_name="gemini-1.5-flash",
    gemini_text_model_name="gemini-pro",
    image_prompt=DEFAULT_IMAGE_PROMPT,
    table_prompt=DEFAULT_TABLE_PROMPT
)

try:
    logger.info(f"Starting markdown processing script with input: {markdown_path}")
    output_path = process_markdown(config)
    logger.info("Script completed successfully")
except Exception as e:
    logger.error(f"Script failed with error: {str(e)}", exc_info=True)
    exit(1)
