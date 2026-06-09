import hashlib
import math
import re

from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    EMBEDDING_DIMENSIONS,
    QWEN_EMBEDDING_BATCH_SIZE,
    QWEN_EMBEDDING_MODEL,
    QWEN_TIMEOUT_SECONDS,
)
from src.openai_compatible_client import OpenAICompatibleClient


class EmbedderAgent:
    def __init__(self):
        self.client = None
        if DASHSCOPE_API_KEY:
            self.client = OpenAICompatibleClient(
                api_key=DASHSCOPE_API_KEY,
                base_url=DASHSCOPE_BASE_URL,
                timeout=QWEN_TIMEOUT_SECONDS,
            )

    def embed_texts(self, text_chunks: list) -> list:
        """Generate embeddings for text chunks."""
        if self.client:
            return self._embed_remote(text_chunks)
        return [self._embed_one(chunk) for chunk in text_chunks]

    def _embed_remote(self, text_chunks: list) -> list:
        vectors = []
        for start in range(0, len(text_chunks), QWEN_EMBEDDING_BATCH_SIZE):
            batch = text_chunks[start : start + QWEN_EMBEDDING_BATCH_SIZE]
            vectors.extend(
                self.client.create_embeddings(
                    model=QWEN_EMBEDDING_MODEL,
                    inputs=batch,
                    dimensions=EMBEDDING_DIMENSIONS,
                )
            )
        return vectors

    def _embed_one(self, text: str) -> list:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
