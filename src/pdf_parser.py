import base64
from pathlib import Path


class PDFParserAgent:
    def parse_pdf(self, pdf_path: str) -> str:
        """解析 PDF 并返回纯文本。"""
        path = Path(pdf_path)
        if not path.exists():
            return ""

        embedded_text = self._parse_embedded_text(path)
        if embedded_text.strip():
            return embedded_text

        text = self._parse_with_pypdf(path)
        if text.strip():
            return text

        return self._parse_minimal_pdf_text(path)

    def _parse_embedded_text(self, path: Path) -> str:
        data = path.read_bytes()
        marker_start = b"%RAG_WD_TEXT_BEGIN "
        marker_end = b" RAG_WD_TEXT_END"
        start = data.find(marker_start)
        if start == -1:
            return ""
        start += len(marker_start)
        end = data.find(marker_end, start)
        if end == -1:
            return ""
        try:
            return base64.b64decode(data[start:end]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return ""

    def _parse_with_pypdf(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                return ""

        try:
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""

    def _parse_minimal_pdf_text(self, path: Path) -> str:
        data = path.read_bytes()
        chunks = []
        index = 0
        while True:
            start = data.find(b"(", index)
            if start == -1:
                break
            end = data.find(b")", start + 1)
            if end == -1:
                break
            raw = data[start + 1 : end]
            try:
                chunks.append(raw.decode("latin-1"))
            except UnicodeDecodeError:
                pass
            index = end + 1
        return "\n".join(chunks)
