import asyncio
import httpx
import json
from app.core.config import settings

async def find_422_triggers_2():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }

    test_payloads = [
        ("role as integer", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": 123, "content": "Hi"}],
        }),
        ("content as dict", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": {"text": "Hi"}}],
        }),
        ("max_tokens as string", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": "1200"
        }),
        ("messages as string", {
            "model": "sarvam-105b-conversations",
            "messages": "Hello"
        }),
        ("null in messages", {
            "model": "sarvam-105b-conversations",
            "messages": [None]
        })
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, payload in test_payloads:
            try:
                res = await client.post(url, headers=headers, json=payload)
                print(f"[{name}] -> Status: {res.status_code}")
                if res.status_code != 200:
                    print(f"   Body: {res.text}")
            except Exception as e:
                print(f"[{name}] -> Exception: {e}")

if __name__ == "__main__":
    asyncio.run(find_422_triggers_2())
