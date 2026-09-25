import asyncio
import httpx
import json
from app.core.config import settings

async def test_sarvam_422():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }
    
    # Test case 1: empty message content
    print("--- 1. Empty message content ---")
    p1 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": "Hello"},
            {"role": "user", "content": ""}
        ]
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r1 = await client.post(url, headers=headers, json=p1)
        print(f"Status: {r1.status_code}, Body: {r1.text}")

    # Test case 2: invalid role
    print("\n--- 2. Invalid role 'bot' ---")
    p2 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": "Hello"},
            {"role": "bot", "content": "Hi"},
            {"role": "user", "content": "How are you?"}
        ]
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r2 = await client.post(url, headers=headers, json=p2)
        print(f"Status: {r2.status_code}, Body: {r2.text}")

    # Test case 3: None content
    print("\n--- 3. None content ---")
    p3 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": "Hello"},
            {"role": "user", "content": None}
        ]
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r3 = await client.post(url, headers=headers, json=p3)
        print(f"Status: {r3.status_code}, Body: {r3.text}")

    # Test case 4: missing system prompt or user prompt
    print("\n--- 4. Empty messages array ---")
    p4 = {
        "model": "sarvam-105b-conversations",
        "messages": []
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r4 = await client.post(url, headers=headers, json=p4)
        print(f"Status: {r4.status_code}, Body: {r4.text}")

if __name__ == "__main__":
    asyncio.run(test_sarvam_422())
