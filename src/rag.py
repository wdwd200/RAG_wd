from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    QWEN_CHAT_MODEL,
    QWEN_MAX_TOKENS,
    QWEN_TEMPERATURE,
    QWEN_TIMEOUT_SECONDS,
    RAG_CONTEXT_MAX_CHARS,
)
from src.openai_compatible_client import OpenAICompatibleClient


class RAGAgent:
    def __init__(self, vector_store, embedder):
        self.vector_store = vector_store
        self.embedder = embedder
        self.client = None
        if DASHSCOPE_API_KEY:
            self.client = OpenAICompatibleClient(
                api_key=DASHSCOPE_API_KEY,
                base_url=DASHSCOPE_BASE_URL,
                timeout=QWEN_TIMEOUT_SECONDS,
            )

    def answer_question(self, question: str, top_k: int = 5) -> str:
        """Retrieve relevant chunks and answer the question."""
        query_vector = self.embedder.embed_texts([question])[0]
        results = self.vector_store.query_vectors(query_vector, top_k)
        if not results:
            return "No relevant content found. Please build the index first."

        if self.client:
            return self._answer_with_chat_model(question, results)

        return self._format_retrieval_results(results)

    def _answer_with_chat_model(self, question: str, results: list) -> str:
        context_blocks = []
        used_chars = 0
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            text = metadata.get("text", "")
            block = (
                f"[{index}] source={metadata.get('source', 'unknown')} "
                f"chunk={metadata.get('chunk_id', index)}\n{text}"
            )
            if used_chars + len(block) > RAG_CONTEXT_MAX_CHARS:
                break
            context_blocks.append(block)
            used_chars += len(block)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a RAG assistant. Answer only from the provided context. "
                    "If the answer is not in the context, say that the indexed documents "
                    "do not contain enough information. Include source chunk numbers."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Context:\n"
                    + "\n\n".join(context_blocks)
                    + f"\n\nQuestion: {question}\nAnswer in Chinese when possible."
                ),
            },
        ]
        answer = self.client.create_chat_completion(
            model=QWEN_CHAT_MODEL,
            messages=messages,
            temperature=QWEN_TEMPERATURE,
            max_tokens=QWEN_MAX_TOKENS,
        )
        return answer.strip()

    def _format_retrieval_results(self, results: list) -> str:
        lines = ["检索到的相关内容："]
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            source = metadata.get("source", "unknown")
            chunk_id = metadata.get("chunk_id", index)
            text = metadata.get("text", "")
            lines.append(f"\n[{index}] source={source}, chunk={chunk_id}, score={result['score']:.4f}")
            lines.append(text)

        return "\n".join(lines)
