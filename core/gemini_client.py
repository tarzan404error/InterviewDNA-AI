import os
import requests


class GeminiClient:
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.base_url = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

    def generate(self, prompt: str, temperature: float = 0.25, max_output_tokens: int = 800) -> str:
        if not self.api_key:
            return None

        url = f"{self.base_url}/models/{self.model}:generateContent"
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            }
        }

        try:
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates") or []
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts") or []
            if not parts:
                return None
            return parts[0].get("text", "").strip()
        except requests.RequestException:
            return None
