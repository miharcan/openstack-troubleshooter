import requests
import os


class OllamaLLM:
    def __init__(
        self,
        model: str | None = None,
        base_url: str = "http://localhost:11434",
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
