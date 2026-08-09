# Internal Architecture & Security

This document outlines the runtime performance characteristics and security mitigations implemented in Markdrop.

---

## Asynchronous Parallel Execution

Converting unstructured, image-heavy documents into enriched text is I/O-bound when calling remote vision APIs. Markdrop processes semantic reasoning concurrently via `asyncio`.

When `markdrop describe` initiates:
1.  **Regex Identification:** Markdrop reads the raw sequence and builds a localized list of pattern-matched image links `![alt](path)` and ASCII representations of `| Tables |`.
2.  **Concurrency Generation:** Both lists map towards unique coroutines (`_replace_image_match()` and `_replace_table_match()`).
3.  **Task Dispatch:** Tasks run inside `asyncio.gather()` pools, bounded by `ProcessorConfig.max_concurrency` (default 8).
4.  **String Reconciliation:** As each description resolves, the enriched document is assembled incrementally.

### Local GPU Workload Protection
Local Hugging Face `transformers` models (like Qwen or Molmo) process inference sequentially on hardware. Running them directly inside the async event loop would block the loop.
*   **Resolution:** Within `models/responder.py`, heavy procedural tasks are wrapped and executed via `await asyncio.to_thread(...)`.

---

## Security Defenses

Markdrop interacts with the filesystem and network when downloading PDFs and reading image assets referenced from Markdown. The following mitigations are implemented in code.

### 1. Server Side Request Forgery (SSRF) Mitigations
`markdrop convert` accepts URLs (e.g. `markdrop convert https://domain.com/paper.pdf`). The `download_pdf()` utility in `utils.py` validates targets before fetching:
*   Only `http://` and `https://` schemes are allowed.
*   The resolved IP is checked with `ipaddress`; private, loopback, and multicast addresses are rejected.
*   Downloads enforce a **200 MB** size cap and a **30 second** timeout.

### 2. Path Traversal Containment
In `markdrop describe`, image paths parsed from Markdown are resolved relative to the input file's directory. Before reading a file, `parse.py` verifies the resolved path remains inside that directory (`str(full).startswith(str(root))`). Attempts outside the directory are logged and skipped.

### 3. Temporary File Handling
`add_downloadable_tables()` builds `.xlsx` files from Pandas dataframes using `tempfile.mkstemp(suffix=".xlsx")` so concurrent runs do not collide on a shared filename.

### 4. API Key Storage
`markdrop setup` writes keys to the user config `.env` file (`~/.config/markdrop/.env` on Linux, `%LOCALAPPDATA%\markdrop\.env` on Windows). On POSIX systems, `os.chmod(env_file, 0o600)` restricts read access to the file owner.
