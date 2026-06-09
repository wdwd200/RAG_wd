import argparse
import json
import re
from pathlib import Path

from config import (
    CHUNKS_FILE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    QWEN_CHAT_MODEL,
    QWEN_MAX_TOKENS,
    QWEN_TEMPERATURE,
    QWEN_TIMEOUT_SECONDS,
    STORAGE_DIR,
)
from src.openai_compatible_client import OpenAICompatibleClient


DEFAULT_OUTPUT = STORAGE_DIR / "eval" / "pdf_eval_dataset.jsonl"


class PDFEvalDatasetBuilder:
    def __init__(self):
        self.client = None
        if DASHSCOPE_API_KEY:
            self.client = OpenAICompatibleClient(
                api_key=DASHSCOPE_API_KEY,
                base_url=DASHSCOPE_BASE_URL,
                timeout=QWEN_TIMEOUT_SECONDS,
            )

    def build(self, output_path: str, questions_per_chunk: int = 2, max_chunks: int = 100) -> list:
        chunks = self._load_chunks()[:max_chunks]
        rows = []

        for chunk in chunks:
            if self.client:
                qa_pairs = self._generate_with_model(chunk, questions_per_chunk)
            else:
                qa_pairs = self._generate_fallback(chunk, questions_per_chunk)

            for item_index, qa in enumerate(qa_pairs, start=1):
                rows.append(
                    {
                        "id": f"{Path(chunk.get('source', 'doc')).stem}-{chunk.get('chunk_id', 0)}-{item_index}",
                        "source": chunk.get("source"),
                        "pdf_path": chunk.get("pdf_path"),
                        "chunk_id": chunk.get("chunk_id"),
                        "question": qa.get("question", "").strip(),
                        "answer": qa.get("answer", "").strip(),
                        "evidence": qa.get("evidence", chunk.get("text", "")[:500]).strip(),
                    }
                )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )
        return rows

    def _load_chunks(self) -> list:
        if not CHUNKS_FILE.exists():
            raise RuntimeError("storage/chunks.json not found. Run: python -m src.app build-index")
        return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))

    def _generate_with_model(self, chunk: dict, questions_per_chunk: int) -> list:
        prompt = f"""
Generate {questions_per_chunk} grounded QA pairs for evaluating a PDF RAG system.
Rules:
- Use only the provided text.
- Questions must be answerable from the text.
- Answers must be concise and factual.
- Evidence must quote or closely paraphrase the exact supporting part.
- Return only a JSON array. Each item must have question, answer, evidence.

Text:
{chunk.get("text", "")}
""".strip()
        content = self.client.create_chat_completion(
            model=QWEN_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=QWEN_TEMPERATURE,
            max_tokens=QWEN_MAX_TOKENS,
        )
        return self._parse_json_array(content)

    def _parse_json_array(self, content: str) -> list:
        content = content.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if fenced:
            content = fenced.group(1).strip()

        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            content = content[start : end + 1]

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to parse QA JSON from model output: {content}") from exc

        if not isinstance(data, list):
            raise RuntimeError("Model output is not a JSON array.")
        return [item for item in data if isinstance(item, dict)]

    def _generate_fallback(self, chunk: dict, questions_per_chunk: int) -> list:
        text = chunk.get("text", "")
        rows = [
            {
                "question": "这段 PDF 内容主要说明了什么？",
                "answer": text[:300],
                "evidence": text[:500],
            }
        ]
        return rows[:questions_per_chunk]


def main():
    parser = argparse.ArgumentParser(description="Build a PDF RAG evaluation dataset")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--questions-per-chunk", type=int, default=2)
    parser.add_argument("--max-chunks", type=int, default=100)
    args = parser.parse_args()

    builder = PDFEvalDatasetBuilder()
    rows = builder.build(
        output_path=args.output,
        questions_per_chunk=args.questions_per_chunk,
        max_chunks=args.max_chunks,
    )
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
