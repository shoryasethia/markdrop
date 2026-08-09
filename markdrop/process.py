import logging
import time
from pathlib import Path

from .config import MarkDropConfig
from .conversion.pipeline import convert_document
from .conversion.types import ConversionResult, DoclingConversionResult
from .process_tables import add_downloadable_tables

logger = logging.getLogger(__name__)


def _convert_with_docling(
    input_doc_path: str,
    output_dir: Path,
    config: MarkDropConfig,
) -> DoclingConversionResult:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

    tables_dir = output_dir / "tables"
    images_dir = output_dir / "images"
    excel_dir = output_dir / config.excel_dir

    for directory in [tables_dir, images_dir, excel_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info("Created directory: %s", directory)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = config.image_resolution_scale
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    logger.info("Starting docling conversion of %s", input_doc_path)
    conv_res = doc_converter.convert(input_doc_path)
    doc_filename = conv_res.input.file.stem

    table_counter = picture_counter = 0

    for element, _level in conv_res.document.iterate_items():
        try:
            if isinstance(element, TableItem):
                table_counter += 1
                element_image_filename = tables_dir / f"{doc_filename}-table-{table_counter}.png"
                with element_image_filename.open("wb") as fp:
                    element.get_image(conv_res.document).save(fp, "PNG")
                logger.debug("Saved table %s", table_counter)

            if isinstance(element, PictureItem):
                picture_counter += 1
                element_image_filename = (
                    images_dir / f"{doc_filename}-picture-{picture_counter}.png"
                )
                with element_image_filename.open("wb") as fp:
                    element.get_image(conv_res.document).save(fp, "PNG")
                logger.debug("Saved picture %s", picture_counter)
        except Exception as e:
            logger.error("Error processing element: %s", e)

    md_filename = output_dir / f"{doc_filename}-markdroped.md"
    html_filename = output_dir / f"{doc_filename}-markdroped.html"

    conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)
    conv_res.document.save_as_html(html_filename, image_mode=ImageRefMode.REFERENCED)

    logger.info("Saved markdown and HTML files")

    with open(html_filename, encoding="utf-8") as file:
        html_content = file.read()

    custom_head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MarkDrop</title>
"""
    html_content = html_content.replace(
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <link rel="icon" type="image/png"\n    href="https://ds4sd.github.io/docling/assets/logo.png"/>',
        custom_head,
    )

    with open(html_filename, "w", encoding="utf-8") as file:
        file.write(html_content)

    return DoclingConversionResult(
        doc_filename=doc_filename,
        md_path=md_filename,
        html_path=html_filename,
        conv_res=conv_res,
        tables_dir=tables_dir,
        images_dir=images_dir,
        table_counter=table_counter,
        picture_counter=picture_counter,
    )


def markdrop(input_doc_path: str, output_dir: str, config: MarkDropConfig | None = None) -> Path:
    """Convert document to markdown and HTML with enhanced features."""
    if config is None:
        config = MarkDropConfig()

    start_time = time.time()
    logger.info("Starting conversion of %s", input_doc_path)

    try:
        result: ConversionResult = convert_document(input_doc_path, output_dir, config)
        elapsed = time.time() - start_time
        logger.info("Document converted and figures exported in %.2f seconds", elapsed)
        return result.html_path
    except Exception as e:
        logger.error("Error in document conversion: %s", e)
        raise


__all__ = [
    "MarkDropConfig",
    "markdrop",
    "add_downloadable_tables",
    "ConversionResult",
    "_convert_with_docling",
]
