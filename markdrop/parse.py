import os
import re
import time
import logging
import shutil
from pathlib import Path
from enum import Enum
import google.generativeai as genai
from openai import OpenAI           #type: ignore
from dotenv import load_dotenv
from PIL import Image
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# Configure logging
def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'markdrop_descriptions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class AIProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"

# Default prompts
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

@dataclass
class ProcessorConfig:
    input_path: str
    output_dir: str
    ai_provider: AIProvider
    remove_images: bool = False
    remove_tables: bool = False
    table_descriptions: bool = True
    image_descriptions: bool = True
    max_retries: int = 3
    retry_delay: int = 2
    gemini_model_name: str = "gemini-1.5-flash"
    gemini_text_model_name: str = "gemini-pro"
    openai_model_name: str = "gpt-4-vision-preview"
    openai_text_model_name: str = "gpt-4-turbo-preview"
    image_prompt: str = DEFAULT_IMAGE_PROMPT
    table_prompt: str = DEFAULT_TABLE_PROMPT

class AIProcessor:
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self._setup_ai_clients()

    def _setup_ai_clients(self):
        """Initialize AI clients based on configuration"""
        load_dotenv()
        
        if self.config.ai_provider == AIProvider.GEMINI:
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")
            genai.configure(api_key=gemini_api_key)
            self.image_model = genai.GenerativeModel(self.config.gemini_model_name)
            self.text_model = genai.GenerativeModel(self.config.gemini_text_model_name)
        
        elif self.config.ai_provider == AIProvider.OPENAI:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in .env file")
            self.client = OpenAI(api_key=openai_api_key)

    def process_image(self, image_path: str) -> str:
        """Process image using selected AI provider"""
        start_time = time.time()
        logger.info(f"Processing image with {self.config.ai_provider}: {image_path}")

        def _process_gemini():
            img = Image.open(image_path)
            response = self.image_model.generate_content([
                self.config.image_prompt,
                img
            ])
            return response.text

        def _process_openai():
            with open(image_path, "rb") as image_file:
                img_data = image_file.read()
            
            response = self.client.chat.completions.create(
                model=self.config.openai_model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.config.image_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_data.hex()}",
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            return response.choices[0].message.content

        try:
            if self.config.ai_provider == AIProvider.GEMINI:
                description = self._process_with_retry(_process_gemini)
            else:
                description = self._process_with_retry(_process_openai)
            
            processing_time = time.time() - start_time
            logger.info(f"Image processed successfully in {processing_time:.2f} seconds")
            return description
        except Exception as e:
            logger.error(f"Final error processing image {image_path}: {str(e)}")
            return f"[Image processing failed for {image_path}]"

    def process_table(self, table_content: str) -> str:
        """Process table using selected AI provider"""
        start_time = time.time()
        logger.info(f"Processing table with {self.config.ai_provider}")

        # Combine prompt with table content
        full_prompt = self.config.table_prompt + table_content

        def _process_gemini():
            response = self.text_model.generate_content(full_prompt)
            return response.text

        def _process_openai():
            response = self.client.chat.completions.create(
                model=self.config.openai_text_model_name,
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content

        try:
            if self.config.ai_provider == AIProvider.GEMINI:
                summary = self._process_with_retry(_process_gemini)
            else:
                summary = self._process_with_retry(_process_openai)
            
            processing_time = time.time() - start_time
            logger.info(f"Table processed successfully in {processing_time:.2f} seconds")
            return summary
        except Exception as e:
            logger.error(f"Final error processing table: {str(e)}")
            return "[Table processing failed]"

    def _process_with_retry(self, func, *args, **kwargs):
        """Generic retry mechanism for processing functions"""
        for attempt in range(self.config.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
                else:
                    logger.error(f"All retry attempts failed")
                    raise

def process_markdown(config: ProcessorConfig):
    """Process markdown file according to provided configuration"""
    total_start_time = time.time()
    logger.info(f"Starting markdown processing with {config.ai_provider}")
    
    input_path = Path(config.input_path)
    output_dir = Path(config.output_dir)
    
    # Initialize AI processor
    ai_processor = AIProcessor(config)
    
    # Validate input file
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create backup of original file
    backup_path = create_backup(input_path)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory confirmed: {output_dir}")
    
    # Create initial processed file
    processed_path = output_dir / f"{input_path.stem}_processed{input_path.suffix}"
    shutil.copy2(backup_path, processed_path)
    logger.info(f"Created initial processed file at: {processed_path}")
    
    # Read the markdown content
    logger.info("Reading markdown file")
    with open(processed_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Process images if enabled
    if config.image_descriptions:
        logger.info("Starting image processing")
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        img_count = len(re.findall(img_pattern, content))
        logger.info(f"Found {img_count} images to process")
        
        def replace_image(match):
            alt_text, image_path = match.groups()
            full_image_path = input_path.parent / image_path
            if full_image_path.exists():
                description = ai_processor.process_image(str(full_image_path))
                if config.remove_images:
                    return f"\n\n**Image Description:** {description}\n\n"
                return f"![{alt_text}]({image_path})\n\n**Image Description:** {description}\n\n"
            logger.warning(f"Image not found: {image_path}")
            return f"[Image not found: {image_path}]"
        
        content = re.sub(img_pattern, replace_image, content)
    else:
        logger.info("Image processing skipped as per configuration")
        img_count = 0
    
    # Process tables if enabled
    if config.table_descriptions:
        logger.info("Starting table processing")
        table_pattern = r'(\|[^\n]+\|\n\|[-:\|\s]+\|\n(?:\|[^\n]+\|\n)+)'
        table_count = len(re.findall(table_pattern, content))
        logger.info(f"Found {table_count} tables to process")
        
        def replace_table(match):
            table_content = match.group(1)
            summary = ai_processor.process_table(table_content)
            if config.remove_tables:
                return f"\n\n**Table Summary:** {summary}\n\n"
            return f"{table_content}\n\n**Table Summary:** {summary}\n\n"
        
        content = re.sub(table_pattern, replace_table, content)
    else:
        logger.info("Table processing skipped as per configuration")
        table_count = 0
    
    # Write processed content to output file
    logger.info(f"Writing processed content to: {processed_path}")
    with open(processed_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    total_time = time.time() - total_start_time
    logger.info(f"Processing complete in {total_time:.2f} seconds")
    logger.info(f"Processed {img_count} images and {table_count} tables")
    logger.info(f"Output saved to: {processed_path}")
    logger.info(f"Original file backed up to: {backup_path}")
    
    return processed_path

def create_backup(file_path):
    """Create a backup of the original file"""
    backup_path = file_path.parent / f"{file_path.stem}_original{file_path.suffix}"
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup at: {backup_path}")
    return backup_path

if __name__ == "__main__":
    # Example usage
    from .process import input_doc_path, output_dir
    
    config = ProcessorConfig(
        input_path=f"{input_doc_path}-markdroped.md",
        output_dir=output_dir,
        ai_provider=AIProvider.GEMINI,  # or AIProvider.OPENAI
        remove_images=False,
        remove_tables=False,
        table_descriptions=True,
        image_descriptions=True
    )
    
    try:
        logger.info("Starting markdown processing script")
        output_path = process_markdown(config)
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed with error: {str(e)}", exc_info=True)
        exit(1)