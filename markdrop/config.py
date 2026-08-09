import logging
from dataclasses import dataclass


@dataclass
class MarkDropConfig:
    """Configuration class for MarkDrop."""

    fast: bool = False
    image_resolution_scale: float = 2.0
    download_button_color: str = "#444444"
    log_level: int = logging.INFO
    log_dir: str = "logs"
    excel_dir: str = "markdrop_excel_tables"
