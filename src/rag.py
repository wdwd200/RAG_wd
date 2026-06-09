class RAGAgent:
    def __init__(self, vector_store, embedder):
        self.vector_store = vector_store
        self.embedder = embedder

    def answer_question(self, question: str, top_k: int = 5) -> str:
        """根据用户问题检索相关文本块并返回答案。"""
        query_vector = self.embedder.embed_texts([question])[0]
        results = self.vector_store.query_vectors(query_vector, top_k)
        if not results:
            return "未检索到相关内容，请先构建索引。"

        lines = ["检索到的相关内容："]
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            source = metadata.get("source", "unknown")
            chunk_id = metadata.get("chunk_id", index)
            text = metadata.get("text", "")
            lines.append(f"\n[{index}] source={source}, chunk={chunk_id}, score={result['score']:.4f}")
            lines.append(text)

        return "\n".join(lines)
