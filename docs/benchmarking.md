# Benchmarking Markdrop

Markdrop can be evaluated on public PDF-to-Markdown benchmarks such as
[OmniDocBench](https://github.com/opendatalab/OmniDocBench) to compare layout
fidelity, table structure, and reading order against other pipelines.

## Quick conversion for benchmark inputs

```bash
# Convert a single PDF (local path or URL)
markdrop convert /path/to/sample.pdf --output_dir ./bench_out

# Optional: export tables and run AI enrichment
markdrop convert /path/to/sample.pdf --output_dir ./bench_out --add_tables
markdrop describe ./bench_out/sample-markdroped.md --provider gemini
```

Each run writes:

- `*-markdroped.md` — primary Markdown output
- `manifest.json` — page classifications, block stats, and stage timings

## OmniDocBench workflow

1. Clone [OmniDocBench](https://github.com/opendatalab/OmniDocBench) and follow
   its dataset preparation instructions.
2. Batch-convert benchmark PDFs with Markdrop:

```bash
for pdf in omnidocbench/pdfs/*.pdf; do
  markdrop convert "$pdf" --output_dir "./omnidoc_out/$(basename "$pdf" .pdf)"
done
```

3. Submit Markdrop Markdown outputs to the OmniDocBench evaluation scripts per
   their README (metrics typically cover text, table, and formula quality).

## Interpreting results

Markdrop is a **hybrid** pipeline (Docling layout + PyMuPDF reconciliation +
optional AI enrichment). Expect strong structure on digital PDFs and academic
papers; scanned documents may need OCR-heavy backends. Compare against:

| Tool | Role |
|------|------|
| Docling | Layout/table backbone used inside Markdrop |
| PyMuPDF4LLM | Fast text-layer extraction, minimal layout |
| Marker | Speed-focused open parser |
| Markdrop | Enriched Markdown/HTML + manifest + optional LLM descriptions |

Report benchmark runs in issues or PRs so results stay reproducible (Python
version, `markdrop --version`, hardware, and whether AI describe was enabled).
