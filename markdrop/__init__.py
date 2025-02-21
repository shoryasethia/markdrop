from pathlib import Path
from .api_setup import setup_apikeys
from .process import markdrop, MarkDropConfig, add_downloadable_tables, logging
from .parse import process_markdown, ProcessorConfig, AIProvider, logger

from .utils import extract_images, make_markdown, extract_tables_from_pdf
from .models.img_descriptions import generate_descriptions
from .models.setup_keys import setup_keys
from .helper import analyze_pdf_images

# Import warnings module for explicit exposure if needed
import warnings
import transformers #type: ignore

# Import and execute warning suppressions
from .ignore_warnings import *

__version__ = "0.3.2.0"

__all__ = [
    # Main processing functions
    'markdrop',
    'process_markdown',
    'add_downloadable_tables',
    
    # Configuration classes
    'MarkDropConfig',
    'ProcessorConfig',
    
    # Utility functions
    'extract_images',
    'make_markdown',
    'extract_tables_from_pdf',
    'generate_descriptions',
    'setup_keys',
    'analyze_pdf_images',
    'setup_apikeys',
    
    # Enums and constants
    'AIProvider',
    
    # Logging and warnings
    'logging',
    'logger',
    'warnings',
    'transformers'
]

# Note: ignore_warnings.py contents are executed on import but don't need
# to be exposed in __all__ since they're just configuration settings
