from config import CHUNK_OVERLAP, CHUNK_SIZE


class SplitterAgent:
    def split_text(self, text: str) -> list:
        """将长文本切分为 500-800 字块，重叠 50-100 字，返回文本块列表。"""
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            end = min(start + CHUNK_SIZE, text_length)
            if end < text_length:
                split_at = normalized.rfind(" ", start, end)
                if split_at > start + 500:
                    end = split_at
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start = max(0, end - CHUNK_OVERLAP)

        return chunks
