"""
markdrop/parse.py
=================
Markdown post-processor that uses AI to generate descriptions for embedded
images and tables.

Supported AI providers
-----------------------
    gemini       – Google Gemini (google-generativeai)
    openai       – OpenAI GPT-4o
    anthropic    – Anthropic Claude (claude-opus-5 / claude-sonnet-5)
    groq         – Groq (llama-4-scout-17b via OpenAI-compatible API)
    openrouter   – OpenRouter (any model via OpenAI-compatible API)
    litellm      – LiteLLM (any 100+ providers via unified interface)
"""

import asyncio
import base64
import logging
import os
import re
import shutil
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from .config_paths import get_gemini_api_key, load_markdrop_env

# ---------------------------------------------------------------------------
# Named logger (handlers are configured in main.py)
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider enum
# ---------------------------------------------------------------------------


class AIProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    LITELLM = "litellm"


# ---------------------------------------------------------------------------
# Default prompts
# ---------------------------------------------------------------------------

DEFAULT_IMAGE_PROMPT = (
    "Provide a detailed, contextually rich description of this image. "
    "Include visual details, context, data, and any relevant information "
    "that would help someone understand what this image conveys without seeing it. "
    "Make it descriptive enough to serve as a replacement for the image."
)

DEFAULT_TABLE_PROMPT = (
    "Analyze this markdown table and provide a detailed description of its contents. "
    "Include key insights, patterns, and important details. Make the summary "
    "comprehensive enough to replace the original table.\n\nTable:\n"
)


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class ProcessorConfig:
    input_path: str
    output_dir: str
    ai_provider: AIProvider
    remove_images: bool = False
    remove_tables: bool = False
    table_descriptions: bool = True
    image_descriptions: bool = True
    max_retries: int = 3
    retry_delay: int = 2
    max_concurrency: int = 8
    timeout_seconds: int = 120

    # ----------------------------------------------------------------
    # Generic override: set either of these to force a specific model
    # for the selected provider (takes precedence over provider-specific
    # model fields below). Useful for the --model CLI flag.
    # ----------------------------------------------------------------
    model_name_override: str = ""  # vision / primary model
    text_model_name_override: str = ""  # text-only model

    # --- Gemini ---
    # gemini-3.1-flash-lite: launched March 3 2026, cost-efficient, low-latency
    # gemini-3.1-pro-preview: Feb 2026 flagship (complex reasoning)
    gemini_model_name: str = "gemini-3.1-flash-lite"
    gemini_text_model_name: str = "gemini-3.1-flash-lite"

    # --- OpenAI ---
    # gpt-5.6-terra: balanced vision + reasoning (Aug 2026 default)
    # gpt-5.6-luna: cost-efficient text/tables; gpt-5.6-sol for max quality
    openai_model_name: str = "gpt-5.6-terra"
    openai_text_model_name: str = "gpt-5.6-luna"

    # --- Anthropic ---
    # claude-opus-5: Jul 2026 flagship vision; claude-sonnet-5 for text/tables
    anthropic_model_name: str = "claude-opus-5"
    anthropic_text_model_name: str = "claude-sonnet-5"

    # --- Groq ---
    # llama-4-maverick: multimodal vision; scout: faster text/tables
    groq_model_name: str = "meta-llama/llama-4-maverick-17b-128e-instruct"
    groq_text_model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # --- OpenRouter (any model on https://openrouter.ai/models) ---
    openrouter_model_name: str = "google/gemini-3.1-flash-lite"
    openrouter_text_model_name: str = "anthropic/claude-sonnet-5"
    openrouter_site_url: str = ""
    openrouter_site_name: str = "markdrop"

    # --- LiteLLM (provider/model format) ---
    litellm_model_name: str = "openai/gpt-5.6-terra"
    litellm_text_model_name: str = "openai/gpt-5.6-luna"

    image_prompt: str = field(default_factory=lambda: DEFAULT_IMAGE_PROMPT)
    table_prompt: str = field(default_factory=lambda: DEFAULT_TABLE_PROMPT)

    # ------------------------------------------------------------------
    # Helpers to resolve the effective model name for the active provider
    # ------------------------------------------------------------------
    def effective_model(self) -> str:
        """Return the vision model to use, respecting --model override."""
        if self.model_name_override:
            return self.model_name_override
        return {
            AIProvider.GEMINI: self.gemini_model_name,
            AIProvider.OPENAI: self.openai_model_name,
            AIProvider.ANTHROPIC: self.anthropic_model_name,
            AIProvider.GROQ: self.groq_model_name,
            AIProvider.OPENROUTER: self.openrouter_model_name,
            AIProvider.LITELLM: self.litellm_model_name,
        }.get(self.ai_provider, "")

    def effective_text_model(self) -> str:
        """Return the text model to use, respecting --text-model override."""
        if self.text_model_name_override:
            return self.text_model_name_override
        return {
            AIProvider.GEMINI: self.gemini_text_model_name,
            AIProvider.OPENAI: self.openai_text_model_name,
            AIProvider.ANTHROPIC: self.anthropic_text_model_name,
            AIProvider.GROQ: self.groq_text_model_name,
            AIProvider.OPENROUTER: self.openrouter_text_model_name,
            AIProvider.LITELLM: self.litellm_text_model_name,
        }.get(self.ai_provider, "")


# ---------------------------------------------------------------------------
# AI Processor
# ---------------------------------------------------------------------------


class AIProcessor:
    def __init__(self, config: ProcessorConfig):
        if not isinstance(config.ai_provider, AIProvider):
            raise TypeError(
                f"config.ai_provider must be an AIProvider enum member, "
                f"got {type(config.ai_provider)}"
            )
        self.config = config
        self._setup_ai_clients()

    # ------------------------------------------------------------------
    # Client initialisation
    # ------------------------------------------------------------------

    def _setup_ai_clients(self):
        """Lazily import and initialise only the required provider client."""
        load_markdrop_env()

        p = self.config.ai_provider
        timeout = self.config.timeout_seconds

        if p == AIProvider.GEMINI:
            from google import genai  # type: ignore

            api_key = get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY (or GOOGLE_API_KEY) not found – run: markdrop setup gemini"
                )
            self.gemini_client = genai.Client(
                api_key=api_key,
                http_options={"timeout": timeout * 1000},
            )

        elif p == AIProvider.OPENAI:
            from openai import OpenAI  # type: ignore

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found – run: markdrop setup openai")
            self.client = OpenAI(api_key=api_key, timeout=timeout)

        elif p == AIProvider.ANTHROPIC:
            import anthropic  # type: ignore

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found – run: markdrop setup anthropic")
            self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

        elif p == AIProvider.GROQ:
            from openai import OpenAI  # type: ignore

            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found – run: markdrop setup groq")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=timeout,
            )

        elif p == AIProvider.OPENROUTER:
            from openai import OpenAI  # type: ignore

            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not found – run: markdrop setup openrouter")
            extra_headers = {}
            if self.config.openrouter_site_url:
                extra_headers["HTTP-Referer"] = self.config.openrouter_site_url
            if self.config.openrouter_site_name:
                extra_headers["X-Title"] = self.config.openrouter_site_name
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers=extra_headers,
                timeout=timeout,
            )

        elif p == AIProvider.LITELLM:
            import litellm  # type: ignore

            self._litellm = litellm

        else:
            raise ValueError(f"Unknown AI provider: {p}")

    # ------------------------------------------------------------------
    # Image processing helpers (one per provider)
    # ------------------------------------------------------------------

    def _encode_image_b64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _image_media_type(self, image_path: str) -> str:
        ext = Path(image_path).suffix.lower().lstrip(".")
        mapping = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "tiff": "image/tiff",
            "bmp": "image/bmp",
        }
        return mapping.get(ext, "image/jpeg")

    async def process_image(self, image_path: str) -> str:
        """Generate a text description for the image at *image_path* asynchronously."""
        start = time.time()
        logger.info(f"Processing image [{self.config.ai_provider.value}]: {image_path}")

        p = self.config.ai_provider

        if p == AIProvider.GEMINI:

            def _call():
                from PIL import Image  # type: ignore

                img = Image.open(image_path)
                response = self.gemini_client.models.generate_content(
                    model=self.config.effective_model(), contents=[self.config.image_prompt, img]
                )
                return response.text
        elif p == AIProvider.OPENAI:

            def _call():
                b64 = self._encode_image_b64(image_path)
                media = self._image_media_type(image_path)
                resp = self.client.chat.completions.create(
                    model=self.config.effective_model(),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.config.image_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{media};base64,{b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                )
                return resp.choices[0].message.content
        elif p == AIProvider.ANTHROPIC:

            def _call():
                b64 = self._encode_image_b64(image_path)
                media = self._image_media_type(image_path)
                resp = self.client.messages.create(
                    model=self.config.effective_model(),
                    max_tokens=500,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media,
                                        "data": b64,
                                    },
                                },
                                {"type": "text", "text": self.config.image_prompt},
                            ],
                        }
                    ],
                )
                return resp.content[0].text
        elif p == AIProvider.GROQ:

            def _call():
                b64 = self._encode_image_b64(image_path)
                media = self._image_media_type(image_path)
                resp = self.client.chat.completions.create(
                    model=self.config.effective_model(),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.config.image_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{media};base64,{b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                )
                return resp.choices[0].message.content
        elif p == AIProvider.OPENROUTER:

            def _call():
                b64 = self._encode_image_b64(image_path)
                media = self._image_media_type(image_path)
                resp = self.client.chat.completions.create(
                    model=self.config.effective_model(),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.config.image_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{media};base64,{b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                )
                return resp.choices[0].message.content
        elif p == AIProvider.LITELLM:

            def _call():
                b64 = self._encode_image_b64(image_path)
                media = self._image_media_type(image_path)
                resp = self._litellm.completion(
                    model=self.config.effective_model(),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.config.image_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{media};base64,{b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                    timeout=self.config.timeout_seconds,
                )
                return resp.choices[0].message.content
        else:
            return f"[Unsupported provider: {p}]"

        try:
            description = await self._process_with_retry(_call)
            logger.info(f"Image processed in {time.time() - start:.2f}s")
            return description
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            return f"[Image processing failed: {image_path}]"

    # ------------------------------------------------------------------
    # Table processing (text-only)
    # ------------------------------------------------------------------

    async def process_table(self, table_content: str) -> str:
        """Generate a text summary for the markdown *table_content* asynchronously."""
        start = time.time()
        full_prompt = self.config.table_prompt + table_content
        p = self.config.ai_provider

        if p == AIProvider.GEMINI:

            def _call():
                response = self.gemini_client.models.generate_content(
                    model=self.config.effective_text_model(), contents=full_prompt
                )
                return response.text
        elif p in (AIProvider.OPENAI, AIProvider.GROQ, AIProvider.OPENROUTER):

            def _call():
                resp = self.client.chat.completions.create(
                    model=self.config.effective_text_model(),
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=500,
                )
                return resp.choices[0].message.content
        elif p == AIProvider.ANTHROPIC:

            def _call():
                resp = self.client.messages.create(
                    model=self.config.effective_text_model(),
                    max_tokens=500,
                    messages=[{"role": "user", "content": full_prompt}],
                )
                return resp.content[0].text
        elif p == AIProvider.LITELLM:

            def _call():
                resp = self._litellm.completion(
                    model=self.config.effective_text_model(),
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=500,
                    timeout=self.config.timeout_seconds,
                )
                return resp.choices[0].message.content
        else:
            return "[Unsupported provider]"

        try:
            summary = await self._process_with_retry(_call)
            logger.info(f"Table processed in {time.time() - start:.2f}s")
            return summary
        except Exception as e:
            logger.error(f"Failed to process table: {e}")
            return "[Table processing failed]"

    # ------------------------------------------------------------------
    # Retry wrapper
    # ------------------------------------------------------------------

    async def _process_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.config.max_retries):
            try:
                # Wrap synchronous API calls inside a thread pool to avoid blocking the event loop
                return await asyncio.to_thread(func, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def process_markdown(config: ProcessorConfig) -> Path:
    """Process a markdown file – generate image/table descriptions via AI asynchronously."""
    start = time.time()
    logger.info(f"Starting markdown processing [{config.ai_provider.value}]")

    input_path = Path(config.input_path)
    output_dir = Path(config.output_dir)

    ai_processor = AIProcessor(config)
    semaphore = asyncio.Semaphore(config.max_concurrency)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    backup_path = create_backup(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_path = output_dir / f"{input_path.stem}_processed{input_path.suffix}"
    shutil.copy2(backup_path, processed_path)

    with open(processed_path, encoding="utf-8") as f:
        content = f.read()

    # ---- images ----
    if config.image_descriptions:
        img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        matches = list(re.finditer(img_pattern, content))
        logger.info(f"Found {len(matches)} images")

        async def _replace_image_match(match):
            async with semaphore:
                alt_text, image_path = match.groups()
                decoded = urllib.parse.unquote(image_path)
                try:
                    root = input_path.parent.resolve()
                    full = (root / decoded).resolve()
                    full.relative_to(root)
                except (ValueError, OSError):
                    logger.warning(f"Blocked path traversal attempt: {image_path}")
                    return match.group(0), "[Image skipped: path outside document directory]"

                if full.exists():
                    desc = await ai_processor.process_image(str(full))
                    if config.remove_images:
                        return match.group(0), f"\n\n**Image Description:** {desc}\n\n"
                    return (
                        match.group(0),
                        f"![{alt_text}]({image_path})\n\n**Image Description:** {desc}\n\n",
                    )

                logger.warning(f"Image not found: {image_path}")
                return match.group(0), f"[Image not found: {image_path}]"

        tasks = [_replace_image_match(m) for m in matches]
        results = await asyncio.gather(*tasks)

        for original_str, new_str in results:
            content = content.replace(original_str, new_str)

        img_count = len(matches)
    else:
        img_count = 0

    # ---- tables ----
    if config.table_descriptions:
        table_pattern = r"(\|[^\n]+\|\n\|[-:\|\s]+\|\n(?:\|[^\n]+\|\n)+)"
        matches = list(re.finditer(table_pattern, content))
        logger.info(f"Found {len(matches)} tables")

        async def _replace_table_match(match):
            async with semaphore:
                table_content = match.group(1)
                summary = await ai_processor.process_table(table_content)
                if config.remove_tables:
                    return match.group(0), f"\n\n**Table Summary:** {summary}\n\n"
                return match.group(0), f"{table_content}\n\n**Table Summary:** {summary}\n\n"

        tasks = [_replace_table_match(m) for m in matches]
        results = await asyncio.gather(*tasks)

        for original_str, new_str in results:
            content = content.replace(original_str, new_str)

        table_count = len(matches)
    else:
        table_count = 0

    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(content)

    elapsed = time.time() - start
    logger.info(
        f"Processing complete in {elapsed:.2f}s – "
        f"{img_count} images, {table_count} tables → {processed_path}"
    )
    return processed_path


def create_backup(file_path: Path) -> Path:
    """Create a timestamped backup so reruns never silently overwrite backups."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}_original_{timestamp}{file_path.suffix}"
    shutil.copy2(file_path, backup_path)
    logger.info(f"Backup created: {backup_path}")
    return backup_path
