# CPU and fast conversion

Markdrop runs on **CPU-only** machines. No NVIDIA GPU is required.

## Recommended: `--fast` mode on CPU

Default conversion loads Docling layout models (Torch, ~GB download, minutes per document).
For quick text extraction on CPU, use fast mode:

```bash
markdrop convert report.pdf --output_dir out --fast
```

Fast mode uses **PyMuPDF only** — typically seconds per document instead of minutes.

| | Default | `--fast` |
|---|---------|----------|
| Engine | Docling + PyMuPDF reconcile | PyMuPDF |
| Torch / ML models | Yes | No |
| Table structure | Yes | No (text layer only) |
| Scanned PDFs / OCR | Docling handles some cases | Poor — use default mode |
| Typical CPU time (15-page paper) | ~2–10 min | ~5–30 sec |

Install optional better Markdown output for fast mode:

```bash
pip install "markdrop[lite]"
```

This adds `pymupdf4llm` for higher-quality Markdown. Without it, Markdrop falls back to block-based text extraction.

## Default mode on CPU

Default mode works on CPU but is slow:

- First run downloads Docling models (one-time, large).
- Expect roughly **8–15 seconds per page** on a modern laptop CPU for digital PDFs.
- A 15-page paper is often **2–5 minutes** after models are cached.

Tips:

- Run once on a small PDF to warm the model cache before batch jobs.
- Use `--fast` when you only need searchable text from digital PDFs.
- Use default mode when tables, figures, and layout matter.

## Google Colab

Colab free tier is CPU or limited GPU. Prefer:

```python
!pip install markdrop
!markdrop convert /content/paper.pdf --output_dir /content/out --fast
```

For full layout quality on Colab, use a GPU runtime and default mode (still slow on first cell).

## Environment variables

No GPU-specific configuration is required. Docling automatically uses CPU when CUDA is unavailable.
