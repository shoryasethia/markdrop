---
name: markdrop
description: Professional AI skill and usage instructions for the Markdrop package, a Python tool for converting PDFs to Markdown/HTML with AI-powered image/table descriptions.
---

# Markdrop Skill

Welcome to the `markdrop` skill. `markdrop` is a powerful Python package and CLI tool used to convert PDF documents into structured Markdown and interactive HTML, while natively leveraging AI vision models to interpret and describe extracted images and tables.

If you are an AI agent or a user aiming to process PDFs and augment them with text or image descriptions, this document serves as your complete guide on utilizing `markdrop` efficiently and accurately.

## 1. Capabilities

- **PDF to Markdown/HTML**: Retains formatting, extracts images, and detects tables via Microsoft Table Transformer and Docling. Supports processing both local file paths and direct PDF URLs.
- **AI Vision Descriptions**: Query GEMINI, OPENAI, ANTHROPIC, GROQ, OPENROUTER, or LITELLM to generate rich descriptions of images and tables.
- **Batch Processing**: Describe entire directories of images in single commands using multiple LLM backends simultaneously.
- **Extensible Configuration**: Precise override control over which structural text-models vs vision-models are used, as well as prompts, resolution scales, and output features.

## 2. API Keys Setup

Before using AI features, API keys must be available in the root `.env` file or environment variables.

If deploying programmatically, you can run the built-in CLI command, or inject them into `os.environ`:
```bash
markdrop setup gemini     # -> GEMINI_API_KEY
markdrop setup openai     # -> OPENAI_API_KEY
markdrop setup anthropic  # -> ANTHROPIC_API_KEY
markdrop setup groq       # -> GROQ_API_KEY
markdrop setup openrouter # -> OPENROUTER_API_KEY
markdrop setup litellm    # -> LITELLM_API_KEY
```

## 3. Python API Integration

The Python API is the recommended way to embed `markdrop` into applications.

### 3.1 PDF Conversion to Interactive HTML
Use `markdrop` function combined with `add_downloadable_tables`:

```python
from markdrop import markdrop, MarkDropConfig, add_downloadable_tables
from pathlib import Path
import logging

# Configuration block
config = MarkDropConfig(
    image_resolution_scale=2.0,
    download_button_color="#444444",
    log_level=logging.INFO,
    log_dir="logs",
    excel_dir="markdrop-excel-tables",
)

# 1. Convert PDF to base HTML (and markdown locally). URL supported here too: "https://url.to/pdf"
html_path = markdrop("path/to/document.pdf", "output_directory", config)

# 2. Enrich HTML to allow downloading tables as Excel sheets
enhanced_html_path = add_downloadable_tables(html_path, config)
```

### 3.2 Injecting AI Descriptions into Markdown
If you have a Markdown file containing image/table links, `process_markdown` automatically routes vision requests to the chosen provider and inserts contextual descriptions.

```python
from markdrop import process_markdown, ProcessorConfig, AIProvider

config = ProcessorConfig(
    input_path="output_directory/document.md",
    output_dir="output_directory",
    ai_provider=AIProvider.GEMINI,  # Available: GEMINI, OPENAI, ANTHROPIC, GROQ, OPENROUTER, LITELLM
    # Target configurations
    remove_images=False,
    remove_tables=False,
    table_descriptions=True,
    image_descriptions=True,
    # Provider-Specific overrides (Optional)
    # Allows granular decoupling of vision parsing vs table text-parsing
    model_name_override="gemini-2.0-flash",  # Primary vision analysis model
    text_model_name_override="gemini-2.0-flash",  # Lean text-only model for generic parsing
)

# Executes AI processing and saves the enriched document
output_path = process_markdown(config)
```

### 3.3 Batch Image Description
For standalone image directories or files:
```python
from markdrop import generate_descriptions

generate_descriptions(
    input_path="images_folder/",
    output_dir="descriptions_output/",
    prompt="Analyze this image and describe all textual and structural elements.",
    llm_client=["gemini", "openai"],
)
```

## 4. CLI Execution Best Practices

As an agent, you can also trigger `markdrop` workflows via Bash.

1. **Convert PDF to MD/HTML (including tables)**:
   ```bash
   markdrop convert <input_path_or_url> --output_dir <dir> --add_tables
   ```

2. **Run AI Provider over the Markdown Output with exact models**:
   ```bash
   markdrop describe <markdown_file> \
       --ai_provider anthropic \
       --model claude-opus-4-6 \
       --text-model claude-sonnet-4-5 \
       --remove_images
   ```

3. **Only Analyze / Extract Images**:
   ```bash
   # Also accepts URLs directly
   markdrop analyze https://domain.com/report.pdf --output_dir pdf_analysis --save_images
   ```

4. **Batch Image Description**:
   ```bash
   markdrop generate images/ --output_dir descriptions/ \
       --prompt "Describe in detail." \
       --llm_client gemini openai
   ```

## 5. Typical Model Fallbacks & Suggestions

- **Default / Cost-Effective**: `gemini` (Gemini 2.0 Flash) is frequently the fastest and cheapest for large scale document evaluation.
- **High Complexity / Intricate Tables**: `anthropic` with the latest Claude models (`claude-opus-4-6` or `claude-sonnet-4-5`) excel in reasoning and formatting.
- **Maximum Speed**: `groq` using LLaMA models.

Whenever instantiating `ProcessorConfig`, be exact about paths—use absolute paths if the current working directory is dynamically changing.
