# Markdrop  

A Python package for converting PDFs (or PDF URLs) to markdown while extracting images and tables. Markdrop makes it easy to convert PDF documents into markdown format while preserving images and tables.  

## Features  

- [x] PDF to Markdown conversion with formatting preservation using Docling
- [x] Automatic image extraction with quality preservation using XRef Id
- [x] Table detection using Microsoft's Table Transformer    
- [x] PDF URL support for above three functionalities
- [ ] Textual descriptive descriptions for extracted images and tables  
- [ ] Optical Character Recognition (OCR) for images with embedded text
- [ ] Enhanced support for structured output formats (e.g., JSON, YAML)    
- [ ] Support for multi-language PDFs  

## Installation  

```bash  
pip install markdrop  
```  
> https://pypi.org/project/markdrop  

## Quick Start  

```python
from markdrop import extract_images, make_markdown, extract_tables_from_pdf

source_pdf = 'path_or_link_to_pdf'  # Replace with your local PDF file path or a URL
output_dir = 'data/output'          # Replace with your local output directory path

# Convert PDF (or URL) to markdown
make_markdown(source_pdf, output_dir)

# Extract images from PDF (or URL)
extract_images(source_pdf, output_dir)

# Extract tables from PDF (or URL)
extract_tables_from_pdf(source_pdf, output_dir=output_dir)
```

## API Reference  

### make_markdown(source, output_dir, verbose=False)  
Converts a PDF or its URL to markdown format.  

Parameters:  
- `source` (str): Path to input PDF or URL  
- `output_dir` (str): Output directory path  
- `verbose` (bool): Enable detailed logging  

### extract_images(source, output_dir, verbose=False)  
Extracts images from PDF or its URL while maintaining quality.  

Parameters:  
- `source` (str): Path to input PDF or URL  
- `output_dir` (str): Output directory path  
- `verbose` (bool): Enable detailed logging  

### extract_tables_from_pdf(pdf_path, **kwargs)  
Detects and extracts tables images.  

Parameters:  
- `pdf_path` (str): Path to input PDF or URL  
- `start_page` (int, optional): Starting page number  
- `end_page` (int, optional): Ending page number  
- `threshold` (float, optional): Detection confidence threshold  
- `output_dir` (str): Output directory path  

## Contributing  

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.  

### Development Setup  

1. Clone the repository:  
```bash  
git clone https://github.com/shoryasethia/markdrop.git  
cd markdrop  
```  

2. Create a virtual environment:  
```bash  
python -m venv venv  
source venv/bin/activate  # On Windows: venv\Scripts\activate  
```  

3. Install development dependencies:  
```bash  
pip install -r requirements.txt  
```  

## Project Structure  

```bash  
markdrop/  
├── LICENSE  
├── README.md  
├── CONTRIBUTING.md  
├── CHANGELOG.md  
├── requirements.txt  
├── setup.py  
└── markdrop/  
    ├── __init__.py  
    ├── main.py  
    ├── utils.py  
    └── ignore_warnings.py  
```  

## License  

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  

## Changelog  

See [CHANGELOG.md](CHANGELOG.md) for version history.  

## Code of Conduct  

Please note that this project follows our [Code of Conduct](CODE_OF_CONDUCT.md).  

## Support  

- [Open an issue](https://github.com/shoryasethia/markdrop/issues)  
