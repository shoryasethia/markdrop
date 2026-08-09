# Changelog

All notable changes to this project will be documented in this file.

## [4.1.2] - Unreleased

### Removed
- GitHub Actions CI workflow and in-repo test suite.

## [4.1.1] - 2026-08-09

### Changed
- Default AI models updated to mid-2026 provider releases: `gpt-5.6-terra` / `gpt-5.6-luna` (OpenAI), `claude-opus-5` / `claude-sonnet-5` (Anthropic), Groq Scout for table text.
- README provider table now lists separate vision vs text defaults.

### Fixed
- Removed broken Star History chart embed (GitHub stargazer API restriction); stars badge at top of README still works.

### Removed
- Unimplemented DOCX/PPTX feature checkbox from README.

## [4.1.0] - 2026-08-09

### Added
- Hybrid conversion pipeline under `markdrop/conversion/` with preflight page classification, Docling + PyMuPDF block reconciliation, and per-run `manifest.json`.
- **`--fast` mode** — PyMuPDF-only conversion for CPU-friendly runs without Docling/Torch.
- **`[lite]` optional extra** — installs `pymupdf4llm` for higher-quality fast-mode Markdown.
- `docs/cpu-guide.md` for CPU-only and Colab usage.
- Public `convert_document()` API returning `ConversionResult`.
- CLI `--version` flag.
- User-level API key storage (`~/.config/markdrop/.env` / `%LOCALAPPDATA%\markdrop\.env`) via `config_paths.py`.
- `examples/quickstart.md` with copy-paste workflow commands.
- `docs/benchmarking.md` with OmniDocBench evaluation workflow ([#13](https://github.com/shoryasethia/markdrop/issues/13)).
- `CODE_OF_CONDUCT.md` (Contributor Covenant) ([#10](https://github.com/shoryasethia/markdrop/issues/10)).
- GitHub Actions CI (Python 3.10–3.13, Ubuntu + Windows: ruff, pytest, build, twine check).
- PEP 621 packaging in `pyproject.toml` with `[dev]` optional dependencies (`pytest`, `pytest-asyncio`, `ruff`, `mypy`).

### Changed
- `markdrop()` delegates through `convert_document()` while preserving `*-markdroped.md/html` outputs and returning the HTML path.
- Remote PDF intake uses hardened download validation (DNS checks, redirect re-validation, size limits, PDF magic-byte verification).
- AI enrichment uses bounded concurrency (`max_concurrency=8`), request timeouts, and pathlib-based path containment.
- API key setup uses hidden `getpass` input instead of echoing keys.
- Package import uses lazy exports; production code no longer injects `MagicMock` modules.
- Documentation aligned with actual output filenames (`*-markdroped.md` / `*-markdroped.html` from `convert`; `{stem}_processed.md` from `describe`).
- API examples updated for async `process_markdown` with `asyncio.run`.
- Model default tables synced to `ProcessorConfig` in `parse.py`.
- Security documentation limited to implemented mitigations (SSRF checks, path traversal guards, download limits, temp file isolation, `.env` permissions).

### Fixed
- LiteLLM table descriptions respect `effective_text_model()` overrides.
- CLI exits non-zero on failure and prints exact output paths.
- Windows URL handling: remote PDFs no longer mangled by `Path()` before download.
- Unified Gemini API key resolution: `GEMINI_API_KEY` with `GOOGLE_API_KEY` fallback ([#8](https://github.com/shoryasethia/markdrop/issues/8)).
- README sync API example incorrectly calling `process_markdown` synchronously.
- Outdated provider model names in docs (e.g. `gpt-4o`, `gemini-2.0-flash`).
- Incorrect API key storage path documented as package install directory.

### Removed
- Legacy `setup.py` (build metadata now lives entirely in `pyproject.toml`).

## [0.1.0] - 24-12-2024
### Added
- Initial release
- PDF to Markdown conversion
- Image extraction functionality
- Table detection using Table Transformer
- Progress tracking with tqdm


## [0.1.1] - 24-12-2024
### Added
- Fix dependency issue. (Added `timm` in `requirements.txt`).

## [0.1.2] - 25-12-2024
### Added
- PDF URL support for pdf to md, images and table extraction.
  
## [0.2.0], [0.2.1] and [0.2.2] - 26-12-2024 - Major Update
### Added
-  Fix downloading pdfs from urls (in `make_markdown`).
-  Added facility to analyze different types of image references (`XRef Id`)in a PDF from local file or URL
-  Now, package supports genration of textual descriptions of image(s).
-  ['qwen', 'gemini', 'openai', 'llama-vision', 'molmo', 'pixtral'] LLM Clients are supported for this conversion

## [0.2.3] to [0.2.7] - 27-12-2024
### Added
-  Fix `img_path` in `responder.py`
-  Optimised `setup_keys` function
-  Enhance and modified `analyze_pdf_images` function

## [0.3.0] - 30-01-2025
### Added
-  End-to-End pdf to markdown
-  End-to-End pdf to html
-  Generate descriptions of images and tables on the fly in a single traversal
-  Added `Download table(s) as Excel` functionality

## [0.3.1] - 30-01-2025
### Added
-  Fix import issue of `Fitz` package

## [0.3.1.1] - 30-01-2025
### Added
-  Fix MarkDropConfig
## [0.3.1.2] - 30-01-2025
### Added
-  Removed conflicts in apikeys setup

## [0.3.4] - 05-07-2025
### Changed
- Deprecated `make_markdown`, `extract_images`, and `extract_tables_from_pdf` functions.
- Improved requirements for better installations.
- Fixed image path error in Gemini description generations.

## [4.1.0] - 09-08-2026
### Added
- Hybrid conversion pipeline with preflight page classification, conversion manifest, and `convert_document()` API.
- GitHub Actions CI across Python 3.10–3.13 on Ubuntu and Windows.
- PEP 621 packaging metadata in `pyproject.toml` with `dev` extras.

### Changed
- Remote PDF intake now uses hardened download validation before conversion.
- API keys are stored in the user config directory with hidden input during setup.
- AI enrichment uses bounded concurrency, request timeouts, and safer path containment.
- Package import no longer injects mock modules for heavy dependencies.

### Fixed
- LiteLLM table descriptions respect text-model overrides.
- CLI reports exact output paths, supports `--version`, and exits non-zero on failures.
- Documentation and quickstart examples now use the real `*-markdroped` output filenames.

## [4.0.2] - 18-03-2026
### Added
- Created comprehensive `SKILL.md` for AI agent integration (`.agent/skills/markdrop/SKILL.md`).
- Documented explicit usage patterns for URL support, extra CLI tools, and `pip install` extensions.

## [0.4.0] - 10-03-2026
### Added
- Anthropic, Groq, OpenRouter, and LiteLLM provider support.
- CLI arguments `--model` and `--text-model` to dynamically override models.
- Support for `[extras]` installation variants (`markdrop[anthropic]`, etc.).

### Changed
- Updated default models to March 2026 flagship/stable versions (`gpt-5.4`, `gemini-3.1-flash-lite`, `claude-opus-4-6`, `meta-llama/llama-4-maverick`).
- Switched default `GOOGLE_API_KEY` to `GEMINI_API_KEY` standard.
- Removed hardcoded module-level variables (e.g. `input_doc_path`) and dead blocks to allow clean importing.
- Changed default encoding logic for image uploads.

### Fixed
- SSRF Vulnerability: Prevented `download_pdf` from hitting private/local IPs.
- Path Traversal: Secured local file reading in `replace_image`.
- DoS Risk: Added 30s timeout and 200MB size limit for PDF downloads.
- Temp File Race Conditions: Enforced secure `tempfile.NamedTemporaryFile` usage.
- File Permissions: Secured auto-generated `.env` files with strict Unix permissions.
- Mutable default arguments in `img_descriptions.py`.