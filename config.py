from pathlib import Path


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
EMBEDDING_DIMENSIONS = 256
