import argparse
import json
from pathlib import Path

from config import BASE_DIR, CHUNKS_FILE, INPUT_DOCS_DIR, PARSED_TEXTS_DIR, SUPPORTED_INPUT_EXTENSIONS
from src.converter import ConverterAgent
from src.embedder import EmbedderAgent
from src.file_detector import FileDetectorAgent
from src.logger import LoggerAgent
from src.pdf_parser import PDFParserAgent
from src.rag import RAGAgent
from src.splitter import SplitterAgent
from src.vector_store import VectorStoreAgent


class AppAgent:
    def __init__(self):
        self.file_detector = FileDetectorAgent()
        self.converter = ConverterAgent()
        self.pdf_parser = PDFParserAgent()
        self.splitter = SplitterAgent()
        self.embedder = EmbedderAgent()
        self.vector_store = VectorStoreAgent()
        self.rag = RAGAgent(self.vector_store, self.embedder)
        self.logger = LoggerAgent()

    def build_index(self):
        """扫描 data/input_docs/，文件检测 -> 转 PDF -> 解析 PDF -> 切片 -> embedding -> 保存向量。"""
        INPUT_DOCS_DIR.mkdir(parents=True, exist_ok=True)
        PARSED_TEXTS_DIR.mkdir(parents=True, exist_ok=True)

        documents = self._iter_input_documents()
        if not documents:
            self.logger.log(f"未发现输入文件，请将 PDF/DOCX/Markdown 放入 {INPUT_DOCS_DIR}")
            self.vector_store.save_vectors([], [])
            self._save_chunks([])
            return

        all_chunks = []
        metadata = []

        for document in documents:
            file_type = self.file_detector.detect_file_type(str(document))
            if file_type == "unsupported":
                self.logger.log(f"跳过不支持的文件: {document}")
                continue

            pdf_path = str(document) if file_type == "pdf" else self.converter.convert_to_pdf(str(document))
            if not pdf_path:
                self.logger.log(f"文件转换失败: {document}")
                continue

            text = self.pdf_parser.parse_pdf(pdf_path)
            if not text.strip():
                self.logger.log(f"PDF 解析为空: {pdf_path}")
                continue

            parsed_path = PARSED_TEXTS_DIR / f"{document.stem}.txt"
            parsed_path.write_text(text, encoding="utf-8")

            chunks = self.splitter.split_text(text)
            for chunk_id, chunk in enumerate(chunks, start=1):
                all_chunks.append(chunk)
                metadata.append(
                    {
                        "source": self._relative_path(document),
                        "pdf_path": self._relative_path(Path(pdf_path)),
                        "parsed_text_path": self._relative_path(parsed_path),
                        "chunk_id": chunk_id,
                        "text": chunk,
                    }
                )

            self.logger.log(f"已处理 {document.name}: {len(chunks)} chunks")

        vectors = self.embedder.embed_texts(all_chunks)
        self.vector_store.save_vectors(vectors, metadata)
        self._save_chunks(metadata)
        self.logger.log(f"索引构建完成: {len(metadata)} chunks")

    def ask(self, question: str, top_k: int = 5):
        """Call RAGAgent.answer_question and print the answer."""
        answer = self.rag.answer_question(question, top_k=top_k)
        print(answer)
        return answer

    def _iter_input_documents(self) -> list:
        return sorted(
            path
            for path in Path(INPUT_DOCS_DIR).iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS
        )

    def _save_chunks(self, metadata: list) -> None:
        CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CHUNKS_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    def _relative_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(BASE_DIR))
        except ValueError:
            return str(path)


def main():
    parser = argparse.ArgumentParser(description="RAG_wd command line")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("build-index", help="Build vector index from data/input_docs")

    ask_parser = subparsers.add_parser("ask", help="Ask a question against the existing index")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--top-k", type=int, default=5)

    subparsers.add_parser("shell", help="Build index and enter interactive question mode")
    args = parser.parse_args()

    app = AppAgent()

    if args.command == "build-index":
        app.build_index()
        return

    if args.command == "ask":
        app.ask(args.question, top_k=args.top_k)
        return

    app.build_index()
    while True:
        question = input("请输入问题（exit 退出）: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if question:
            app.ask(question)


if __name__ == "__main__":
    main()
