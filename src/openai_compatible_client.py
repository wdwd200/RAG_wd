import json
from urllib import error, request


class OpenAICompatibleClient:
    def __init__(self, api_key: str, base_url: str, timeout: int = 60):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def create_embeddings(self, model: str, inputs: list, dimensions: int) -> list:
        payload = {
            "model": model,
            "input": inputs,
            "dimensions": dimensions,
            "encoding_format": "float",
        }
        response = self._post("/embeddings", payload)
        rows = sorted(response.get("data", []), key=lambda item: item.get("index", 0))
        return [row["embedding"] for row in rows]

    def create_chat_completion(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self._post("/chat/completions", payload)
        choices = response.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return message.get("content", "")

    def _post(self, path: str, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Model API request failed: HTTP {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Model API request failed: {exc.reason}") from exc
