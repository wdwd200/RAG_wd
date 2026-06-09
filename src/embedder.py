import hashlib
import math
import re

from config import EMBEDDING_DIMENSIONS


class EmbedderAgent:
    def embed_texts(self, text_chunks: list) -> list:
        """将文本块生成向量 embedding，返回向量列表。"""
        return [self._embed_one(chunk) for chunk in text_chunks]

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
