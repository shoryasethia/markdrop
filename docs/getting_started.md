# Getting Started with Markdrop

Welcome to Markdrop! Markdrop is a high-performance Python toolkit designed to bridge the gap between complex PDF research documents and modern, AI-powered markup. It extracts text and preserves precise formatting and tabular structures, while asynchronously enriching the content using state-of-the-art Multi-Modal Language Models.

This guide will walk you through setting up Markdrop, configuring your preferred AI providers, and running your first end-to-end PDF processing pipeline.

## 1. Installation & Environment Setup

Markdrop requires **Python 3.10+**. It relies on several core dependencies like `docling`, `beautifulsoup4`, and `google-genai`.

### Core Installation
To install the core package (which includes built-in support for Google Gemini and OpenAI):
```bash
pip install markdrop
```

### Provider-Specific Extensions
Markdrop supports various AI providers. Depending on which models you plan to run, you can install the required SDKs via extras:

*   **Anthropic Claude:** `pip install "markdrop[anthropic]"`
*   **Groq (Llama Models):** `pip install "markdrop[groq]"`
*   **LiteLLM (Universal Gateway):** `pip install "markdrop[litellm]"`
*   **Local Models (Ollama):** `pip install "markdrop[local-models]"`

> **Tip:** To install all dependencies at once, run `pip install "markdrop[all]"`. Note that **OpenRouter** is supported out-of-the-box via the `openai` SDK.

Check your installed version at any time:

```bash
markdrop --version
```

## 2. Configuring API Keys

Markdrop needs API keys to communicate with AI providers for generating image and table descriptions. Keys are stored in a user-level `.env` file (not inside the package install directory).

Use the `setup` command to interactively configure your keys:

```bash
markdrop setup gemini
```

The CLI prompts for your key using hidden input (`getpass`). Once entered, the key is saved to:

*   **Linux/macOS:** `~/.config/markdrop/.env` (or `$XDG_CONFIG_HOME/markdrop/.env` when set)
*   **Windows:** `%LOCALAPPDATA%\markdrop\.env`

On POSIX systems, the file is written with `0o600` permissions so only the owner can read it.

You can repeat this process for any provider you wish to use:
*   `markdrop setup openai`
*   `markdrop setup anthropic`
*   `markdrop setup groq`
*   `markdrop setup openrouter`
*   `markdrop setup litellm`

## 3. Your First End-to-End Workflow

The typical Markdrop workflow involves two distinct steps:
1.  **Extraction:** Converting the raw binary PDF file into a standard Markdown (`.md`) file and an interactive HTML viewer.
2.  **Enrichment:** Parsing the generated Markdown to find images and tables, and asking an AI Vision model to generate semantic descriptions to replace or augment those raw elements.

### Step 3.1: Converting the PDF (`convert`)

Use the `convert` command to ingest a local PDF file or a public HTTPS link. URL downloads are validated with SSRF checks before fetching.

```bash
markdrop convert https://arxiv.org/pdf/1706.03762 --output_dir my_research --add_tables
```

**What happens here:**
1.  Markdrop downloads the PDF (blocking private/loopback addresses).
2.  It uses `docling` to extract headings, paragraphs, lists, equations, tables, and images.
3.  It scales and saves extracted images to `my_research/images/`.
4.  It writes a structured `1706.03762-markdroped.md` file.
5.  It generates an interactive `1706.03762-markdroped.html` file.
6.  The `--add_tables` flag evaluates all datatables and embeds downloadable Excel (`.xlsx`) workbooks directly into the HTML view.

### Step 3.2: Adding AI Descriptions (`describe`)

Now that you have a Markdown file full of `![image](...)` links and raw Markdown tables, you can enrich it.

```bash
markdrop describe my_research/1706.03762-markdroped.md --ai_provider gemini --remove_images
```

**What happens here:**
1.  Markdrop parses the markdown and discovers all image links and markdown tables.
2.  It uses `asyncio` to concurrently dispatch requests to the configured provider (default vision model: `gemini-3.1-flash-lite`).
3.  Each image is encoded and sent to the vision model with a prompt to describe it in detail.
4.  Each table is sent to the text model to generate a concise summary of the data.
5.  The original markdown is updated. Because we passed `--remove_images`, the raw `![image](...)` syntax is stripped and entirely replaced by the AI's semantic text description. This is extremely useful when preparing document sets for RAG pipelines or LLM training.
6.  The result is saved as `1706.03762-markdroped_processed.md` in the output directory.

## Next Steps

Now that you've run the core pipeline, dive deeper into the specific features:

*   **[CLI Reference](cli_reference.md)**: Explore the detailed configuration flags for every command.
*   **[Python API Reference](api_reference.md)**: Learn how to import Markdrop classes to build custom data integration pipelines.
*   **[Providers & Models](providers.md)**: Discover how to override default models, configure Groq/LiteLLM, and leverage local multimodal models like Molmo or Pixtral.
*   **[Architecture & Security](architecture.md)**: Understand the async processing loop and implemented security guards.
*   **[Quickstart](../examples/quickstart.md)**: Copy-paste commands for the full workflow.
