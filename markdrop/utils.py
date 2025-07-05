
import pymupdf as fitz
import os
import pandas as pd
from bs4 import BeautifulSoup
import base64
import openpyxl
import requests
from tqdm import tqdm
import logging
import time
from pathlib import Path

# Configure logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'markdrop_{time.strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def download_pdf(url, download_dir):
    """Download PDF from a URL with progress bar"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get filename from URL
        filename = url.split('/')[-1]
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        file_path = os.path.join(download_dir, filename)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(file_path, 'wb') as f, tqdm(
            desc=f"Downloading {filename}",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
                bar.update(len(data))
        
        logger.info(f"Successfully downloaded PDF to {file_path}")
        return file_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF from {url}: {e}")
        raise

def cleanup_download_dir(download_dir, verbose=False):
    """Clean up downloaded PDF files"""
    try:
        for filename in os.listdir(download_dir):
            file_path = os.path.join(download_dir, filename)
            os.remove(file_path)
            if verbose:
                logger.info(f"Removed temporary file: {file_path}")
        os.rmdir(download_dir)
        if verbose:
            logger.info(f"Removed temporary directory: {download_dir}")
    except Exception as e:
        logger.error(f"Error cleaning up download directory: {e}")
