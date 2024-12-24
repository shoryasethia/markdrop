# Markdrop

A Python package for converting PDFs to markdown while extracting images and tables. Markdrop makes it easy to convert PDF documents into markdown format while preserving images and tables.

## Features

- PDF to Markdown conversion with formatting preservation using Docling
- Automatic image extraction with quality preservation using XRef Id
- Table detection using Microsoft's Table Transformer

## Installation

```bash
pip install markdrop
```

## Quick Start

```python
from markdrop import extract_images, make_markdown, extract_tables_from_pdf

# Convert PDF to markdown
make_markdown("input.pdf", "output_dir")

# Extract images
extract_images("input.pdf", "output_dir")

# Extract tables
extract_tables_from_pdf("input.pdf", output_dir="output_dir")
```

## API Reference

### make_markdown(source, output_dir, verbose=False)
Converts a PDF to markdown format.

Parameters:
- `source` (str): Path to input PDF
- `output_dir` (str): Output directory path
- `verbose` (bool): Enable detailed logging

### extract_images(source, output_dir, verbose=False)
Extracts images from PDF while maintaining quality.

Parameters:
- `source` (str): Path to input PDF
- `output_dir` (str): Output directory path
- `verbose` (bool): Enable detailed logging

### extract_tables_from_pdf(pdf_path, **kwargs)
Detects and extracts tables using AI.

Parameters:
- `pdf_path` (str): Path to input PDF
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
pip install -r requirements-dev.txt
```

### Running Tests
```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Code of Conduct

Please note that this project follows our [Code of Conduct](CODE_OF_CONDUCT.md).

## Support

- [Open an issue](https://github.com/shoryasethia/markdrop/issues)
- [Documentation](https://markdrop.readthedocs.io/)