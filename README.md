# Markdrop  

A Python package for converting PDFs (or PDF URLs) to markdown while extracting images and tables. Markdrop makes it easy to convert PDF documents into markdown format while preserving images and tables.  

## Features  

- [x] PDF to Markdown conversion with formatting preservation using Docling
- [x] Automatic image extraction with quality preservation using XRef Id
- [x] Table detection using Microsoft's Table Transformer    
- [x] PDF URL support for above three functionalities
- [x] Textual descriptive descriptions for any image file or folder  
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

source_pdf = 'url/or/path/to/pdf/file'    # Replace with your local PDF file path or a URL
output_dir = 'data/output'                # Replace it with desired output directory's path

make_markdown(source_pdf, output_dir)
extract_images(source_pdf, output_dir)
extract_tables_from_pdf(source_pdf, output_dir=output_dir)

```

```python
from markdrop import setup_keys

### API Key Setup
### If using 'openai' or 'gemini' as llm_client in the generate_descriptions function, you need to set up the API keys first.

setup_keys(key = 'google')
```

```python
from markdrop import generate_descriptions

### Image Descriptions Generation

prompt = "Give textual highly detailed descriptions from this image ONLY, nothing else." # Replace it with your desired prompt
input_path = 'path/to/img_file/or/dir'         # Replace it with the path to the images dir or image file
output_dir = 'data/output'                     # Replace it with the desired output directory's path
llm_clients = ['gemini','llama-vision']        # Replace it with the desired models from ['qwen', 'gemini', 'openai', 'llama-vision', 'molmo', 'pixtral'] only

generate_descriptions(input_path = input_path, output_dir = output_dir, prompt = prompt, llm_client = llm_clients)
```
```python
from markdrop import analyze_pdf_images

pdf_path = 'path/to/pdf/file'             # Replace with your local PDF file pathL
output_dir = "output/data/image_xref"     # Replace it with desired output directory's path

analyze_pdf_images(pdf_path, output_dir, verbose=True, save_images=True)
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

### setup_keys(key)
Generates the description of image(s) based on given prompt and llm_client in a csv
> `llm clients` supported are ['qwen', 'gemini', 'openai', 'llama-vision', 'molmo', 'pixtral']

Parameters:
- `key` (str): `key = 'google'` if using `'gemini'` as llm_client in generate_descriptions
- `key` (str): `key = 'openai'` if using `'openai'` as llm_client in generate_descriptions

### generate_descriptions(input_path, output_dir, prompt, llm_client)
Generates the description of image(s) based on given prompt and llm_client in a csv
> `llm clients` supported are ['qwen', 'gemini', 'openai', 'llama-vision', 'molmo', 'pixtral']

Parameters:
- `input_path` (str): Path to input PDF or URL  
- `output_dir` (str): Output directory path  
- `prompt` (str): prompt to be sent to model along with image
- `llm_client` (list): list containing minimum one model from llm clients


### analyze_pdf_images(source: str, output_dir: str, verbose = False, save_images = False):
Analyze different types of image references in a PDF and save results
    
Parameters:  
- `source` (str): Local PDF path or URL to PDF
- `output_dir` (str): Directory for saving analysis results and extracted images
- `verbose` (bool): Print detailed information
- `save_images` (bool): If True, saves extracted images to output_dir


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
    ├── helper.py
    ├── ignore_warnings.py
    └── models/
        ├── __init__.py
        ├── .env
        ├── img_descriptions.py
        ├── logger.py
        ├── model_loader.py
        ├── responder.py
        └── setup_keys.py  
```  

## License  

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  

## Changelog  

See [CHANGELOG.md](CHANGELOG.md) for version history.  

## Code of Conduct  

Please note that this project follows our [Code of Conduct](CODE_OF_CONDUCT.md).  

## Support  

- [Open an issue](https://github.com/shoryasethia/markdrop/issues)  
