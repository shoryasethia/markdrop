import base64
import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from .config import MarkDropConfig

logger = logging.getLogger(__name__)


def add_downloadable_tables(html_path: Path, config: MarkDropConfig | None = None) -> Path:
    """Add downloadable table functionality to HTML file."""
    if config is None:
        config = MarkDropConfig()

    with open(html_path, encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    if not soup.head:
        soup.html.insert(0, soup.new_tag("head"))
    if not soup.body:
        if soup.html:
            soup.html.append(soup.new_tag("body"))
        else:
            html_tag = soup.new_tag("html")
            body_tag = soup.new_tag("body")
            html_tag.append(body_tag)
            soup.append(html_tag)

    jszip_script = soup.new_tag(
        "script", src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"
    )
    soup.head.append(jszip_script)

    download_all_div = soup.new_tag("div", style="text-align: center; margin: 20px 0;")
    download_all_button = soup.new_tag(
        "button",
        style=(
            f"background-color: {config.download_button_color}; color: white; "
            "padding: 12px 24px; border: none; border-radius: 5px; "
            "cursor: pointer; font-weight: bold;"
        ),
    )
    download_all_button["onclick"] = "downloadAllTablesAsZip()"
    download_all_button.string = "Download All Tables as Excel"
    download_all_div.append(download_all_button)

    if soup.body.contents:
        soup.body.insert(0, download_all_div)
    else:
        soup.body.append(download_all_div)

    script_tag = soup.new_tag("script")
    script_tag.string = """
    function downloadExcel(data, filename) {
        const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function base64ToExcel(base64Data) {
        const binary = atob(base64Data);
        const array = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            array[i] = binary.charCodeAt(i);
        }
        return array;
    }

    async function downloadAllTablesAsZip() {
        const zip = new JSZip();
        const excelFolder = zip.folder("markdrop_excel_tables");
        const tables = document.querySelectorAll('.table-data');
        for (let i = 0; i < tables.length; i++) {
            const base64Data = tables[i].getAttribute('data-excel');
            excelFolder.file(`table-${i + 1}.xlsx`, base64ToExcel(base64Data));
        }
        const zipBlob = await zip.generateAsync({type: "blob"});
        const link = document.createElement('a');
        link.href = URL.createObjectURL(zipBlob);
        link.download = "markdrop_excel_tables.zip";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    """

    for idx, table in enumerate(soup.find_all("table"), 1):
        try:
            rows = table.find_all("tr")
            if not rows:
                continue

            table_data = []
            max_cols = 0
            for row in rows:
                cells = row.find_all(["th", "td"])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    table_data.append(row_data)
                    max_cols = max(max_cols, len(row_data))

            if not table_data:
                continue

            table_data = [row + [""] * (max_cols - len(row)) for row in table_data]
            headers = [f"Column{i + 1}" for i in range(max_cols)]
            if any(cell.name == "th" for cell in rows[0].find_all(["th", "td"])):
                headers = table_data[0]
                table_data = table_data[1:]

            df = pd.DataFrame(table_data, columns=headers)
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
            os.close(tmp_fd)
            try:
                with pd.ExcelWriter(tmp_path, engine="openpyxl") as excel_writer:
                    df.to_excel(excel_writer, index=False)
                with open(tmp_path, "rb") as handle:
                    excel_data = handle.read()
            finally:
                os.unlink(tmp_path)

            base64_excel = base64.b64encode(excel_data).decode()
            download_div = soup.new_tag("div", style="margin: 10px 0; text-align: right;")
            download_button = soup.new_tag(
                "button",
                style=(
                    f"background-color: {config.download_button_color}; color: white; "
                    "padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;"
                ),
            )
            download_button["onclick"] = (
                f'downloadExcel(base64ToExcel("{base64_excel}"), "table-{idx}.xlsx")'
            )
            download_button.string = "Download Table as Excel"
            table_data_div = soup.new_tag(
                "div", **{"class": "table-data", "style": "display: none;"}
            )
            table_data_div["data-excel"] = base64_excel
            download_div.append(download_button)
            download_div.append(table_data_div)
            table.insert_after(download_div)
        except Exception as exc:
            logger.error("Error processing table %s: %s", idx, exc)

    soup.head.append(script_tag)
    output_path = html_path.parent / f"{html_path.stem}_download_tables.html"
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(str(soup))
    return output_path
