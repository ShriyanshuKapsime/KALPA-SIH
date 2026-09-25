import asyncio
import httpx
import json
from app.core.config import settings

async def find_422_triggers():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }

    test_payloads = [
        ("response_format json_object", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "response_format": {"type": "json_object"}
        }),
        ("temperature > 2.0", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": 5.0
        }),
        ("max_tokens negative", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": -5
        }),
        ("unsupported param 'stream_options'", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream_options": {"include_usage": True}
        }),
        ("unsupported param 'user'", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "user": "test-user-id"
        }),
        ("extra field in message", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi", "name": "Alice"}]
        }),
        ("reasoning_effort", {
            "model": "sarvam-105b-conversations",
            "messages": [{"role": "user", "content": "Hi"}],
            "reasoning_effort": "high"
        }),
        ("empty messages array", {
            "model": "sarvam-105b-conversations",
            "messages": []
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
    asyncio.run(find_422_triggers())
