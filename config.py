import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DOCS_DIR = DATA_DIR / "input_docs"

STORAGE_DIR = BASE_DIR / "storage"
CONVERTED_PDFS_DIR = STORAGE_DIR / "converted_pdfs"
PARSED_TEXTS_DIR = STORAGE_DIR / "parsed_texts"
INDEX_DIR = STORAGE_DIR / "index"
CHUNKS_FILE = STORAGE_DIR / "chunks.json"
VECTORS_FILE = INDEX_DIR / "vectors.json"

SUPPORTED_INPUT_EXTENSIONS = {".pdf", ".docx", ".md"}

CHUNK_SIZE = 700
CHUNK_OVERLAP = 80
EMBEDDING_DIMENSIONS = int(os.getenv("QWEN_EMBEDDING_DIMENSIONS", "1024"))

_raw_dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_API_KEY = "" if _raw_dashscope_api_key == "replace-with-your-api-key" else _raw_dashscope_api_key
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_CHAT_MODEL = os.getenv("QWEN_CHAT_MODEL", "qwen-plus")
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v4")
QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.2"))
QWEN_MAX_TOKENS = int(os.getenv("QWEN_MAX_TOKENS", "1500"))
QWEN_TIMEOUT_SECONDS = int(os.getenv("QWEN_TIMEOUT_SECONDS", "60"))
QWEN_EMBEDDING_BATCH_SIZE = int(os.getenv("QWEN_EMBEDDING_BATCH_SIZE", "10"))
RAG_CONTEXT_MAX_CHARS = int(os.getenv("RAG_CONTEXT_MAX_CHARS", "6000"))
