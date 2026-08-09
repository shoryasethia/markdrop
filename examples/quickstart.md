# Quickstart

```bash
pip install markdrop
markdrop convert report.pdf --output_dir out
```

Fast mode on CPU (no Docling/Torch):

```bash
markdrop convert report.pdf --output_dir out --fast
```

Generated files:

- `out/report-markdroped.md`
- `out/report-markdroped.html`
- `out/images/` and `out/tables/`
- `out/manifest.json`

Optional table downloads in HTML:

```bash
markdrop convert report.pdf --output_dir out --add_tables
```

AI enrichment (requires API key setup):

```bash
markdrop setup gemini
markdrop describe out/report-markdroped.md --ai_provider gemini --output_dir out/enriched
```

Python API:

```python
import asyncio
from markdrop import convert_document, MarkDropConfig, process_markdown, ProcessorConfig, AIProvider

result = convert_document("report.pdf", "out", MarkDropConfig())
print(result.markdown_path, result.html_path)


async def enrich():
    config = ProcessorConfig(
        input_path=str(result.markdown_path),
        output_dir="out/enriched",
        ai_provider=AIProvider.GEMINI,
    )
    return await process_markdown(config)


asyncio.run(enrich())
```
