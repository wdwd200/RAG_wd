# AGENTS.md - Strict Execution Guide

## 项目概览

**项目名称**：RAG_wd  
**目标**：实现可直接运行的 RAG 系统，支持 PDF 文档解析，并将 Word/Markdown 文件统一转换为 PDF 后解析。Codex 按文档严格生成代码，不允许自由发挥。

**项目结构**：

```
RAG_wd/
  data/
    input_docs/
  storage/
    converted_pdfs/
    parsed_texts/
    index/
    chunks.json
  src/
    file_detector.py
    converter.py
    pdf_parser.py
    splitter.py
    embedder.py
    vector_store.py
    rag.py
    logger.py
    app.py
  config.py
```

## Agent 文件和类说明

### 1. FileDetectorAgent (file_detector.py)

```python
class FileDetectorAgent:
    def detect_file_type(self, file_path: str) -> str:
        """判断文件类型，返回 'pdf' / 'docx' / 'md' / 'unsupported'"""
        pass
```

### 2. ConverterAgent (converter.py)

```python
class ConverterAgent:
    def convert_to_pdf(self, file_path: str) -> str:
        """将 docx 或 md 文件转换为 PDF，返回 PDF 文件路径，失败返回 None"""
        pass
```

### 3. PDFParserAgent (pdf_parser.py)

```python
class PDFParserAgent:
    def parse_pdf(self, pdf_path: str) -> str:
        """解析 PDF 并返回纯文本"""
        pass
```

### 4. SplitterAgent (splitter.py)

```python
class SplitterAgent:
    def split_text(self, text: str) -> list:
        """将长文本切分为 500-800 字块，重叠 50-100 字，返回文本块列表"""
        pass
```

### 5. EmbedderAgent (embedder.py)

```python
class EmbedderAgent:
    def embed_texts(self, text_chunks: list) -> list:
        """将文本块生成向量 embedding，返回向量列表"""
        pass
```

### 6. VectorStoreAgent (vector_store.py)

```python
class VectorStoreAgent:
    def save_vectors(self, vectors: list, metadata: list) -> None:
        """保存向量及元数据"""
        pass

    def query_vectors(self, query_vector: list, top_k: int) -> list:
        """返回 top_k 相似文本块及元数据"""
        pass
```

### 7. RAGAgent (rag.py)

```python
class RAGAgent:
    def __init__(self, vector_store: VectorStoreAgent, embedder: EmbedderAgent):
        pass

    def answer_question(self, question: str, top_k: int = 5) -> str:
        """根据用户问题检索相关文本块并调用 LLM 返回答案"""
        pass
```

### 8. LoggerAgent (logger.py)

```python
class LoggerAgent:
    def log(self, message: str) -> None:
        """统一记录错误/信息到控制台或文件"""
        pass
```

### 9. AppAgent (app.py)

```python
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
        """扫描 data/input_docs/，文件检测 → 转 PDF → 解析 PDF → 切片 → embedding → 保存向量"""
        pass

    def ask(self, question: str):
        """调用 RAGAgent.answer_question 并输出答案"""
        pass
```

## 主流程调用顺序

1. AppAgent.build_index() 构建向量索引
2. AppAgent.ask(question) 提问
3. 内部依次调用：FileDetectorAgent → ConverterAgent → PDFParserAgent → SplitterAgent → EmbedderAgent → VectorStoreAgent → RAGAgent → LoggerAgent

**提示**：Codex 严格按照文件、类和函数签名生成代码，不做自由发挥。