import importlib
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "4.1.1"

__all__ = [
    # Main processing functions
    "convert_document",
    "ConversionResult",
    "markdrop",
    "process_markdown",
    "add_downloadable_tables",
    # Configuration classes
    "MarkDropConfig",
    "ProcessorConfig",
    # AI provider enum
    "AIProvider",
    # Utility functions
    "generate_descriptions",
    "setup_keys",
    "analyze_pdf_images",
    "download_pdf",
    "cleanup_download_dir",
    # Version
    "__version__",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "convert_document": (".conversion", "convert_document"),
    "ConversionResult": (".conversion", "ConversionResult"),
    "markdrop": (".process", "markdrop"),
    "add_downloadable_tables": (".process", "add_downloadable_tables"),
    "MarkDropConfig": (".config", "MarkDropConfig"),
    "process_markdown": (".parse", "process_markdown"),
    "ProcessorConfig": (".parse", "ProcessorConfig"),
    "AIProvider": (".parse", "AIProvider"),
    "generate_descriptions": (".models.img_descriptions", "generate_descriptions"),
    "setup_keys": (".setup_keys", "setup_keys"),
    "analyze_pdf_images": (".helper", "analyze_pdf_images"),
    "download_pdf": (".utils", "download_pdf"),
    "cleanup_download_dir": (".utils", "cleanup_download_dir"),
}


def __getattr__(name: str):
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_IMPORTS[name]
    module = importlib.import_module(module_name, __package__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
