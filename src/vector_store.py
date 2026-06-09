import json
import math
from pathlib import Path

from config import VECTORS_FILE


class VectorStoreAgent:
    def __init__(self):
        self.vectors = []
        self.metadata = []
        self.storage_path = Path(VECTORS_FILE)
        self._load()

    def save_vectors(self, vectors: list, metadata: list) -> None:
        """保存向量及元数据。"""
        self.vectors = vectors
        self.metadata = metadata
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(
            json.dumps({"vectors": vectors, "metadata": metadata}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def query_vectors(self, query_vector: list, top_k: int) -> list:
        """返回 top_k 相似文本块及元数据。"""
        if not query_vector:
            return []

        scored = []
        for vector, item in zip(self.vectors, self.metadata):
            score = self._cosine_similarity(query_vector, vector)
            scored.append({"score": score, "metadata": item})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.vectors = payload.get("vectors", [])
        self.metadata = payload.get("metadata", [])

    def _cosine_similarity(self, left: list, right: list) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)
