import json
from pathlib import Path

from config import CHUNKS_FILE, INPUT_DOCS_DIR, PARSED_TEXTS_DIR, SUPPORTED_INPUT_EXTENSIONS
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
                        "source": str(document),
                        "pdf_path": pdf_path,
                        "parsed_text_path": str(parsed_path),
                        "chunk_id": chunk_id,
                        "text": chunk,
                    }
                )

            self.logger.log(f"已处理 {document.name}: {len(chunks)} chunks")

        vectors = self.embedder.embed_texts(all_chunks)
        self.vector_store.save_vectors(vectors, metadata)
        self._save_chunks(metadata)
        self.logger.log(f"索引构建完成: {len(metadata)} chunks")

    def ask(self, question: str):
        """调用 RAGAgent.answer_question 并输出答案。"""
        answer = self.rag.answer_question(question)
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


def main():
    app = AppAgent()
    app.build_index()
    while True:
        question = input("请输入问题（exit 退出）: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if question:
            app.ask(question)


if __name__ == "__main__":
    main()
