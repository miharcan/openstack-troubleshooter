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
        print("\n[DEBUG] Ollama model:", self.model)
        print("[DEBUG] Prompt sent to Ollama (first 500 chars):")
        print(prompt[:500], "\n")

        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        print("[DEBUG] HTTP status:", resp.status_code)
        resp.raise_for_status()

        data = resp.json()
        text = data.get("response", "").strip()

        print("[DEBUG] Ollama response (first 500 chars):")
        print(text[:500], "\n")

        return text
