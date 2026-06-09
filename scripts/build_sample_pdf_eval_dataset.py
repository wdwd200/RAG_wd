import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.converter import ConverterAgent

INPUT_DIR = ROOT / "data" / "input_docs"
EVAL_DIR = ROOT / "storage" / "eval"
DATASET_PATH = EVAL_DIR / "pdf_eval_dataset.jsonl"


DOCUMENTS = [
    {
        "stem": "RAG架构基础",
        "title": "RAG 架构基础",
        "body": [
            "检索增强生成系统通常包含三个主要阶段：索引构建、问题检索和答案生成。",
            "在索引构建阶段，系统会把文档解析成文本，切分成文本块，生成向量，并连同元数据一起保存。",
            "在问题检索阶段，系统会把用户问题转换成向量，并与已保存的文档向量比较，选出最相关的文本块。",
            "在答案生成阶段，聊天模型会把检索到的文本块作为上下文，并且应该只根据这些上下文回答。",
            "有用的元数据包括源文件路径、文本块编号、可用时的页码，以及原始文本片段。",
        ],
        "qa": [
            {
                "question": "RAG 系统通常包含哪三个主要阶段？",
                "answer": "RAG 系统通常包含索引构建、问题检索和答案生成三个阶段。",
                "evidence": "检索增强生成系统通常包含三个主要阶段：索引构建、问题检索和答案生成。",
            },
            {
                "question": "索引构建阶段会对文档做哪些处理？",
                "answer": "系统会把文档解析成文本，切分成文本块，生成向量，并连同元数据一起保存。",
                "evidence": "在索引构建阶段，系统会把文档解析成文本，切分成文本块，生成向量，并连同元数据一起保存。",
            },
            {
                "question": "RAG 文本块适合保存哪些元数据？",
                "answer": "适合保存源文件路径、文本块编号、可用时的页码以及原始文本片段。",
                "evidence": "有用的元数据包括源文件路径、文本块编号、可用时的页码，以及原始文本片段。",
            },
        ],
    },
    {
        "stem": "PDF评测数据集规范",
        "title": "PDF 评测数据集规范",
        "body": [
            "PDF 评测数据集应该包含问题、参考答案，以及来自源文档的证据片段。",
            "每个答案都应该绑定一段简短证据，这样可以分别检查检索质量和生成质量。",
            "问题类型应该覆盖事实、定义、比较和流程步骤，而不是只重复一种简单问法。",
            "数据集应该避免提出需要外部知识的问题，因为这些信息并不存在于已索引的 PDF 文档中。",
            "JSONL 是一种方便的存储格式，因为每一行都可以表示一条独立的评测样本。",
        ],
        "qa": [
            {
                "question": "PDF 评测数据集应该包含哪些内容？",
                "answer": "应该包含问题、参考答案，以及来自源文档的证据片段。",
                "evidence": "PDF 评测数据集应该包含问题、参考答案，以及来自源文档的证据片段。",
            },
            {
                "question": "为什么每个答案都应该绑定证据？",
                "answer": "因为这样可以分别检查检索质量和生成质量。",
                "evidence": "每个答案都应该绑定一段简短证据，这样可以分别检查检索质量和生成质量。",
            },
            {
                "question": "为什么 JSONL 适合保存评测数据集？",
                "answer": "因为每一行都可以表示一条独立的评测样本。",
                "evidence": "JSONL 是一种方便的存储格式，因为每一行都可以表示一条独立的评测样本。",
            },
        ],
    },
    {
        "stem": "千问配置指南",
        "title": "千问配置指南",
        "body": [
            "项目会从本地 .env 文件或环境变量中读取 DashScope 配置。",
            "DASHSCOPE_API_KEY 用来保存 API Key，这个 Key 同时用于 embedding 请求和聊天模型请求。",
            "QWEN_EMBEDDING_MODEL 用来选择 embedding 模型，默认示例配置使用 text-embedding-v4。",
            "QWEN_CHAT_MODEL 用来选择聊天模型，该模型负责根据检索上下文生成最终答案。",
            "如果没有配置 API Key，项目仍然可以使用本地兜底 embedding 运行，但不会启用模型生成答案。",
        ],
        "qa": [
            {
                "question": "项目会从哪里读取 DashScope 配置？",
                "answer": "项目会从本地 .env 文件或环境变量中读取 DashScope 配置。",
                "evidence": "项目会从本地 .env 文件或环境变量中读取 DashScope 配置。",
            },
            {
                "question": "DASHSCOPE_API_KEY 有什么作用？",
                "answer": "它用来保存 API Key，并同时用于 embedding 请求和聊天模型请求。",
                "evidence": "DASHSCOPE_API_KEY 用来保存 API Key，这个 Key 同时用于 embedding 请求和聊天模型请求。",
            },
            {
                "question": "没有配置 API Key 时项目会怎样运行？",
                "answer": "项目仍然可以使用本地兜底 embedding 运行，但不会启用模型生成答案。",
                "evidence": "如果没有配置 API Key，项目仍然可以使用本地兜底 embedding 运行，但不会启用模型生成答案。",
            },
        ],
    },
]


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    converter = ConverterAgent()

    rows = []
    for document in DOCUMENTS:
        markdown_path = INPUT_DIR / f"{document['stem']}.md"
        markdown_text = "# " + document["title"] + "\n\n" + "\n\n".join(document["body"]) + "\n"
        markdown_path.write_text(markdown_text, encoding="utf-8")

        pdf_path = Path(converter.convert_to_pdf(str(markdown_path)))
        target_pdf_path = INPUT_DIR / f"{document['stem']}.pdf"
        if target_pdf_path.exists():
            target_pdf_path.unlink()
        pdf_path.replace(target_pdf_path)
        markdown_path.unlink()

        for index, qa in enumerate(document["qa"], start=1):
            rows.append(
                {
                    "id": f"{document['stem']}-{index}",
                    "source": str(target_pdf_path.relative_to(ROOT)),
                    "pdf_path": str(target_pdf_path.relative_to(ROOT)),
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "evidence": qa["evidence"],
                }
            )

    DATASET_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(DOCUMENTS)} PDFs to {INPUT_DIR}")
    print(f"Wrote {len(rows)} evaluation rows to {DATASET_PATH}")


if __name__ == "__main__":
    main()
