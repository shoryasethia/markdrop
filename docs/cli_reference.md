# Detailed CLI Reference

The Markdrop Command Line Interface (CLI) is the primary way to interact with the toolkit. It is executed using the `markdrop` prefix and offers five distinct subcommands: `convert`, `describe`, `analyze`, `setup`, and `generate`.

---

## Global Options

```bash
markdrop --version
```

Prints the installed package version (for example `markdrop 4.1.2`).

---

## 1. `markdrop convert`

The `convert` command turns a flat PDF binary into structured digital text (Markdown) and visualization (HTML).

### Syntax
```bash
markdrop convert <input_path> [--output_dir <dir>] [--add_tables] [--fast]
```

### Arguments
*   **`input_path` (Required)**: The source PDF. This can be:
    *   An absolute path (e.g., `/Users/name/docs/paper.pdf`)
    *   A relative path (e.g., `./paper.pdf`)
    *   A web URL (e.g., `https://arxiv.org/pdf/1234.5678.pdf`). `download_pdf()` blocks private, loopback, and multicast addresses before fetching.
*   **`--output_dir` (Optional)**: The directory where the generated files should be saved. Defaults to `./output`. If the directory doesn't exist, Markdrop will create it.
*   **`--add_tables` (Optional)**: Parses extracted Markdown tables, creates formatted Excel (`.xlsx`) workbooks for each one, and embeds interactive "Download Excel" buttons within the generated HTML viewer.
*   **`--fast` (Optional)**: PyMuPDF-only conversion. Skips Docling/Torch for much faster CPU runs. No ML table detection; poor on scanned PDFs. Install `markdrop[lite]` for `pymupdf4llm` Markdown quality.

### Output Behavior
Assuming `--output_dir out` and input `report.pdf`, Markdrop generates:
1.  `out/report-markdroped.md`: The raw structured text.
2.  `out/report-markdroped.html`: A styled, interactive HTML webpage mirroring the document.
3.  `out/images/`: A folder containing all high-resolution images extracted from the PDF pages.

---

## 2. `markdrop describe`

The `describe` command scans an existing Markdown file, identifies image tags and data tables, and asynchronously generates detailed semantic summaries for them using AI models.

### Syntax
```bash
markdrop describe <input_path> \
    [--output_dir <dir>] \
    [--ai_provider <provider>] \
    [--model <model_name>] \
    [--text-model <text_model_name>] \
    [--remove_images] \
    [--remove_tables]
```

### Arguments
*   **`input_path` (Required)**: The path to the Markdown file you wish to process (usually the `*-markdroped.md` file from `convert`).
*   **`--output_dir` (Optional)**: Directory to save the processed file. Defaults to `./output`. The output filename is `{stem}_processed.md` (e.g., `report-markdroped_processed.md`).
*   **`--ai_provider` (Optional)**: Specifies which LLM backend to use. Defaults to `gemini`.
    *   Valid options: `gemini`, `openai`, `anthropic`, `groq`, `openrouter`, `litellm`.
*   **`--model` (Optional)**: Overrides the default vision model used by the selected provider.
    *   Example: `--model gemini-3.1-pro-preview` or `--model gpt-5.6-sol`.
*   **`--text-model` (Optional)**: Overrides the default text model used for summarizing data tables. Defaults are provider-specific (see [providers.md](providers.md)).
*   **`--remove_images` (Optional)**: If set, Markdrop deletes the raw `![alt](image_path.jpg)` syntax entirely from the Markdown doc, substituting it cleanly with `**Image Description:** [Generated AI Text]`. This is critical when normalizing documents for ingestion into vector databases that cannot process image binaries.
*   **`--remove_tables` (Optional)**: Similarly, if set, deletes the raw ASCII markdown table entirely in favor of an AI-generated paragraph summarizing the data trends.

---

## 3. `markdrop setup`

The `setup` command stores API keys in your user config directory.

### Syntax
```bash
markdrop setup <provider>
```

### Arguments
*   **`provider` (Required)**: The provider you wish to configure.
    *   Valid options: `gemini`, `openai`, `anthropic`, `groq`, `openrouter`, `litellm`.

### Behavior
The CLI interactively prompts for your API key (hidden input). Keys are written to:

*   **Linux/macOS:** `~/.config/markdrop/.env`
*   **Windows:** `%LOCALAPPDATA%\markdrop\.env`

On POSIX systems, Markdrop applies `os.chmod(env_file, 0o600)` so only the executing user can read the file.

---

## 4. `markdrop analyze`

The `analyze` command is a targeted utility focused exclusively on image extraction, bypassing the entire Markdown/HTML document generation pipeline.

### Syntax
```bash
markdrop analyze <input_path> [--output_dir <dir>] [--save_images]
```

### Arguments
*   **`input_path` (Required)**: Path or URL to the PDF.
*   **`--output_dir` (Optional)**: Where to store output. Defaults to `output/analysis/`.
*   **`--save_images` (Optional)**: If passed, physically writes the extracted pixel data to the disk. Otherwise, it merely logs the image metadata (dimensions, bounding boxes, page references).

---

## 5. `markdrop generate`

The `generate` command is a batch processing utility. If you already have a folder full of raw images (whether from PDFs or elsewhere) and want to run a custom multimodal query against all of them, use this tool.

### Syntax
```bash
markdrop generate <input_path> \
    [--output_dir <dir>] \
    [--prompt <custom_prompt>] \
    [--llm_client <client_list...>]
```

### Arguments
*   **`input_path` (Required)**: A path to a specific image file OR a path to a directory containing `.jpg`, `.png`, `.webp`, etc.
*   **`--output_dir` (Optional)**: Defaults to `output/descriptions/`.
*   **`--prompt` (Optional)**: The system prompt supplied to the Vision model alongside the image.
    *   Default: *"Describe the image in detail."*
    *   Example: `--prompt "Transcribe all hand-written notes in this image EXACTLY as written. Output only the transcription."`
*   **`--llm_client` (Optional)**: A space-separated list of models to evaluate. Markdrop will run the prompt against *every* image with *every* model provided in this list, allowing you to benchmark model accuracy against your specific prompt.
    *   Valid options: `qwen`, `gemini`, `openai`, `llama-vision`, `molmo`, `pixtral`.
    *   Default: `gemini`

### Output Behavior
It evaluates all images and generates a consolidated CSV file: `responses_YYYYMMDD_HHMMSS.csv` containing columns for `image_path`, `model`, and `response`.
