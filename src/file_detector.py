from pathlib import Path


class FileDetectorAgent:
    def detect_file_type(self, file_path: str) -> str:
        """判断文件类型，返回 'pdf' / 'docx' / 'md' / 'unsupported'。"""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return "pdf"
        if suffix == ".docx":
            return "docx"
        if suffix == ".md":
            return "md"
        return "unsupported"
