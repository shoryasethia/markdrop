# Supported AI Providers & Model Configuration

Markdrop operates agnostic to the underlying AI model processing document images and tables. When you execute `markdrop describe`, the system finds image binaries and table formats, packages that data for the selected provider SDK, and generates semantic summaries.

Default model names are defined in `markdrop/parse.py` on `ProcessorConfig`.

---

## Default Providers

If you do not override manually, these are the models Markdrop uses:

| Provider Flag | Network | Vision Model (Images) | Text Model (Tables) | Notes |
| --- | --- | --- | --- | --- |
| `--ai_provider gemini` | Google | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | Built on `google-genai` SDK. Default provider. |
| `--ai_provider openai` | OpenAI | `gpt-5.6-terra` | `gpt-5.6-luna` | Terra for vision; Luna for table text. |
| `--ai_provider anthropic` | Anthropic | `claude-opus-5` | `claude-sonnet-5` | Opus for vision; Sonnet for table text. |
| `--ai_provider groq` | Groq | `meta-llama/llama-4-maverick-17b-128e-instruct` | `meta-llama/llama-4-scout-17b-16e-instruct` | Maverick vision; Scout text. |
| `--ai_provider openrouter` | OpenRouter | `google/gemini-3.1-flash-lite` | `anthropic/claude-sonnet-5` | Any model string from openrouter.ai/models. |
| `--ai_provider litellm` | LiteLLM | `openai/gpt-5.6-terra` | `openai/gpt-5.6-luna` | `provider/model` format; set downstream keys in env. |

---

## API & CLI Model Overrides

You can override models dynamically:

### Via the CLI
Use `--model` for the primary vision model and `--text-model` for table summarization.

```bash
markdrop describe out/report-markdroped.md \
    --ai_provider anthropic \
    --model claude-sonnet-5 \
    --text-model claude-haiku-3-5
```

### Via the Python API
```python
config = ProcessorConfig(
    input_path="file.md",
    output_dir="out",
    ai_provider=AIProvider.OPENAI,
    openai_model_name="gpt-5.6-terra",
    openai_text_model_name="gpt-5.6-luna",
)
```

Or use generic overrides (same as CLI flags):

```python
config = ProcessorConfig(
    input_path="file.md",
    output_dir="out",
    ai_provider=AIProvider.OPENAI,
    model_name_override="gpt-5.6-terra",
    text_model_name_override="gpt-5.6-luna",
)
```

---

## Platform Proxies (Universal Access)

### OpenRouter (`--ai_provider openrouter`)
OpenRouter proxies many LLM APIs over an OpenAI-compatible interface. Override the model with `--model` or `openrouter_model_name`:

```bash
markdrop describe out/report-markdroped.md \
    --ai_provider openrouter \
    --model "x-ai/grok-vision-beta"
```

### LiteLLM (`--ai_provider litellm`)
LiteLLM routes to downstream providers. Set the relevant API keys in your environment or user config `.env`, then pass `provider/model` strings:

```python
config = ProcessorConfig(
    input_path="file.md",
    output_dir="out",
    ai_provider=AIProvider.LITELLM,
    litellm_model_name="mistral/pixtral-large-2411",
)
```

---

## Local Models

Markdrop's `generate` command supports evaluating isolated images against local PyTorch models via `transformers` on your GPU.

These local endpoints are not used for bulk Markdown enrichment in `describe`, but are available for benchmarking in `models/responder.py`:
1.  **Qwen** (`model_choice='qwen'`): Utilizes `qwen_vl_utils`.
2.  **LLaMA Vision** (`model_choice='llama-vision'`).
3.  **Molmo** (`model_choice='molmo'`): Half-precision inference utilizing Hugging Face configurations.
4.  **Pixtral** (`model_choice='pixtral'`).

```python
from markdrop import generate_descriptions

generate_descriptions(
    input_path="eval_dataset/",
    output_dir="local_results/",
    prompt="Identify object.",
    llm_client=["molmo"],
)
```
