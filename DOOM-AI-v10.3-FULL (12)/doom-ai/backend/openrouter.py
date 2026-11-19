"""
DOOM AI — OpenRouter client
Single responsibility: call OpenRouter and return text.
"""
import httpx
from main import settings

async def call_model(model: str, prompt: str, temperature: float = 0.6) -> str:
    if not settings.openrouter_api_key or settings.openrouter_api_key.startswith("sk-or-v1-your"):
        return f"[demo · {model}] {prompt[:160]}"

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{settings.openrouter_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "https://doom.ai",
                "X-Title": "DOOM AI",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            },
        )
        if resp.status_code != 200:
            return f"Error from {model}: {resp.status_code}"
        data = resp.json()
        return data["choices"][0]["message"]["content"]
