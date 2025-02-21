import logging
import time
from pathlib import Path

from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


import os
import pandas as pd
from bs4 import BeautifulSoup
import base64
import openpyxl
from dataclasses import dataclass
from typing import Optional


input_doc_path = "path/to/input.pdf"
output_dir = Path('output_dir')


@dataclass
class MarkDropConfig:
    """Configuration class for MarkDrop"""
    image_resolution_scale: float = 2.0
    download_button_color: str = '#444444'
    favicon_link: str = 'src/markdrop-logo.png'
    log_level: int = logging.INFO
    log_dir: str = 'logs'
    excel_dir: str = 'markdrop_excel_tables'

def setup_logging(config: MarkDropConfig) -> None:
    """Set up logging configuration"""
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f'markdrop_{time.strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=config.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def markdrop(input_doc_path: str, output_dir: str, config: Optional[MarkDropConfig] = None) -> Path:
    """
    Convert document to markdown and HTML with enhanced features
    """
    if config is None:
        config = MarkDropConfig()
    
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    output_dir = Path(output_dir)
    tables_dir = output_dir / "tables"
    images_dir = output_dir / "images"
    excel_dir = output_dir / config.excel_dir
    
    # Create directories
    for directory in [tables_dir, images_dir, excel_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

    # Configure pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = config.image_resolution_scale
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = time.time()
    logger.info(f"Starting conversion of {input_doc_path}")

    try:
        conv_res = doc_converter.convert(input_doc_path)
        doc_filename = conv_res.input.file.stem

        table_counter = picture_counter = 0
        
        # Process tables and pictures
        for element, _level in conv_res.document.iterate_items():
            try:
                if isinstance(element, TableItem):
                    table_counter += 1
                    element_image_filename = tables_dir / f"{doc_filename}-table-{table_counter}.png"
                    with element_image_filename.open("wb") as fp:
                        element.get_image(conv_res.document).save(fp, "PNG")
                    logger.debug(f"Saved table {table_counter}")

                if isinstance(element, PictureItem):
                    picture_counter += 1
                    element_image_filename = images_dir / f"{doc_filename}-picture-{picture_counter}.png"
                    with element_image_filename.open("wb") as fp:
                        element.get_image(conv_res.document).save(fp, "PNG")
                    logger.debug(f"Saved picture {picture_counter}")
            except Exception as e:
                logger.error(f"Error processing element: {e}")

        # Save markdown and HTML
        md_filename = output_dir / f"{doc_filename}-markdroped.md"
        html_filename = output_dir / f"{doc_filename}-markdroped.html"
        
        conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)
        conv_res.document.save_as_html(html_filename, image_mode=ImageRefMode.REFERENCED)
        
        logger.info(f"Saved markdown and HTML files")

        # Modify HTML content
        with open(html_filename, 'r', encoding='utf-8') as file:
            html_content = file.read()

        custom_head = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <link rel="icon" href="src/markdrop-logo.png" type="image/png">
    <meta charset="UTF-8">
    <title>MarkDrop</title>
'''
        html_content = html_content.replace('<!DOCTYPE html>\n<html lang="en">\n<head>\n    <link rel="icon" type="image/png"\n    href="https://ds4sd.github.io/docling/assets/logo.png"/>', custom_head)

        with open(html_filename, 'w', encoding='utf-8') as file:
            file.write(html_content)

        end_time = time.time() - start_time
        logger.info(f"Document converted and figures exported in {end_time:.2f} seconds")
        
        return html_filename

    except Exception as e:
        logger.error(f"Error in document conversion: {e}")
        raise

def add_downloadable_tables(html_path: Path, config: Optional[MarkDropConfig] = None) -> Path:
    """
    Add downloadable table functionality to HTML file with improved table processing
    """
    if config is None:
        config = MarkDropConfig()
    
    logger = logging.getLogger(__name__)
    
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ensure HTML structure exists
        if not soup.head:
            soup.html.insert(0, soup.new_tag('head'))
        if not soup.body:
            if soup.html:
                soup.html.append(soup.new_tag('body'))
            else:
                html_tag = soup.new_tag('html')
                body_tag = soup.new_tag('body')
                html_tag.append(body_tag)
                soup.append(html_tag)
        
        # Add JSZip library
        jszip_script = soup.new_tag('script', src='https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js')
        soup.head.append(jszip_script)
        
        # Add download all button
        download_all_div = soup.new_tag('div', style='text-align: center; margin: 20px 0;')
        download_all_button = soup.new_tag('button',
            style=f'background-color: {config.download_button_color}; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;')
        download_all_button['onclick'] = 'downloadAllTablesAsZip()'
        download_all_button.string = 'Download All Tables as Excel'
        download_all_div.append(download_all_button)
        
        if soup.body.contents:
            soup.body.insert(0, download_all_div)
        else:
            soup.body.append(download_all_div)
        
        # Add JavaScript functions
        script_tag = soup.new_tag('script')
        script_tag.string = '''
        function downloadExcel(data, filename) {
            const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        function base64ToExcel(base64Data) {
            const binary = atob(base64Data);
            const array = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                array[i] = binary.charCodeAt(i);
            }
            return array;
        }
        
        async function downloadAllTablesAsZip() {
            const zip = new JSZip();
            const excelFolder = zip.folder("markdrop_excel_tables");
            
            const tables = document.querySelectorAll('.table-data');
            for (let i = 0; i < tables.length; i++) {
                const base64Data = tables[i].getAttribute('data-excel');
                const excelData = base64ToExcel(base64Data);
                excelFolder.file(`table-${i + 1}.xlsx`, excelData);
            }
            
            const zipBlob = await zip.generateAsync({type: "blob"});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(zipBlob);
            link.download = "markdrop_excel_tables.zip";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        '''
        
        # Process tables (rest of the code remains the same)
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables to process")
        
        for idx, table in enumerate(tables, 1):
            try:
                # Extract table data with improved header handling
                rows = table.find_all('tr')
                if not rows:
                    logger.warning(f"No rows found in table {idx}")
                    continue
                
                # Process all rows as data first
                table_data = []
                max_cols = 0
                
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        table_data.append(row_data)
                        max_cols = max(max_cols, len(row_data))
                
                if not table_data:
                    logger.warning(f"No data extracted from table {idx}")
                    continue
                
                # Ensure all rows have the same number of columns
                table_data = [row + [''] * (max_cols - len(row)) for row in table_data]
                
                # Generate headers based on first row or column numbers
                headers = [f'Column{i+1}' for i in range(max_cols)]
                if any(cell.name == 'th' for cell in rows[0].find_all(['th', 'td'])):
                    headers = table_data[0]
                    table_data = table_data[1:]
                
                # Create DataFrame
                df = pd.DataFrame(table_data, columns=headers)
                
                # Save Excel file using context manager
                with pd.ExcelWriter('temp.xlsx', engine='openpyxl') as excel_writer:
                    df.to_excel(excel_writer, index=False)
                
                # Read the saved Excel file
                with open('temp.xlsx', 'rb') as f:
                    excel_data = f.read()
                os.remove('temp.xlsx')
                
                base64_excel = base64.b64encode(excel_data).decode()
                
                # Create download button for individual table
                download_div = soup.new_tag('div', style='margin: 10px 0; text-align: right;')
                download_button = soup.new_tag('button',
                    style=f'background-color: {config.download_button_color}; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;')
                download_button['onclick'] = f'downloadExcel(base64ToExcel("{base64_excel}"), "table-{idx}.xlsx")'
                download_button.string = 'Download Table as Excel'
                
                # Add hidden div with table data
                table_data_div = soup.new_tag('div', **{'class': 'table-data', 'style': 'display: none;'})
                table_data_div['data-excel'] = base64_excel
                
                download_div.append(download_button)
                download_div.append(table_data_div)
                table.insert_after(download_div)
                
                logger.debug(f"Successfully processed table {idx}")
                
            except Exception as e:
                logger.error(f"Error processing table {idx}: {e}")
                continue
        
        # Add script to head
        soup.head.append(script_tag)
        
        # Save modified HTML
        output_path = html_path.parent / f"{html_path.stem}_download_tables.html"
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        
        logger.info(f"Created downloadable tables HTML at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error in adding downloadable tables: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    # Create custom configuration (optional)
    config = MarkDropConfig(
        image_resolution_scale=2.5,
        download_button_color='#444444',
        log_level=logging.DEBUG
    )
    
    # Convert document
    input_doc_path = input_doc_path
    output_dir = output_dir
    
    # Use with default config
    html_path = markdrop(input_doc_path, output_dir)
    
    # Or use with custom config
    # html_path = markdrop(input_doc_path, output_dir, config)
    
    # Add downloadable tables
    downloadable_html = add_downloadable_tables(html_path, config)
