import base64
import html
import shutil
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from config import CONVERTED_PDFS_DIR


class ConverterAgent:
    def convert_to_pdf(self, file_path: str) -> str:
        """将 docx 或 md 文件转换为 PDF，返回 PDF 文件路径，失败返回 None。"""
        source = Path(file_path)
        if not source.exists():
            return None

        CONVERTED_PDFS_DIR.mkdir(parents=True, exist_ok=True)
        target = CONVERTED_PDFS_DIR / f"{source.stem}.pdf"

        if source.suffix.lower() == ".pdf":
            return str(source)

        if self._convert_with_libreoffice(source, target):
            return str(target)

        fallback_text = self._extract_text(source)
        if not fallback_text:
            return None

        return self._write_minimal_pdf(fallback_text, target)

    def _convert_with_libreoffice(self, source: Path, target: Path) -> bool:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            return False

        try:
            subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(target.parent),
                    str(source),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return False

        generated = target.parent / f"{source.stem}.pdf"
        return generated.exists()

    def _extract_text(self, source: Path) -> str:
        if source.suffix.lower() == ".md":
            return source.read_text(encoding="utf-8", errors="ignore")
        if source.suffix.lower() == ".docx":
            return self._extract_docx_text(source)
        return ""

    def _extract_docx_text(self, source: Path) -> str:
        try:
            with zipfile.ZipFile(source) as archive:
                xml_data = archive.read("word/document.xml")
        except (KeyError, OSError, zipfile.BadZipFile):
            return ""

        try:
            root = ElementTree.fromstring(xml_data)
        except ElementTree.ParseError:
            return ""

        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs)

    def _write_minimal_pdf(self, text: str, target: Path) -> str:
        lines = []
        for raw_line in text.splitlines():
            clean_line = html.unescape(raw_line).strip()
            if clean_line:
                lines.append(clean_line)
        if not lines:
            lines = ["Empty document"]

        content_lines = ["BT", "/F1 12 Tf", "50 780 Td"]
        for index, line in enumerate(lines[:55]):
            safe = self._escape_pdf_text(line[:100])
            if index:
                content_lines.append("0 -16 Td")
            content_lines.append(f"({safe}) Tj")
        content_lines.append("ET")
        content = "\n".join(content_lines).encode("latin-1", errors="replace")

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
        ]

        buffer = bytearray(b"%PDF-1.4\n")
        offsets = []
        for number, obj in enumerate(objects, start=1):
            offsets.append(len(buffer))
            buffer.extend(f"{number} 0 obj\n".encode("ascii"))
            buffer.extend(obj)
            buffer.extend(b"\nendobj\n")

        xref_start = len(buffer)
        buffer.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        buffer.extend(b"0000000000 65535 f \n")
        for offset in offsets:
            buffer.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        buffer.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n".encode("ascii")
        )

        encoded_text = base64.b64encode(text.encode("utf-8")).decode("ascii")
        buffer.extend(f"\n%RAG_WD_TEXT_BEGIN {encoded_text} RAG_WD_TEXT_END\n".encode("ascii"))
        target.write_bytes(buffer)
        return str(target)

    def _escape_pdf_text(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
