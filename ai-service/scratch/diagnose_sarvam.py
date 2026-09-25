import asyncio
import httpx
import json
from app.core.config import settings

async def test_sarvam():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }
    
    print(f"API Key configured: {bool(settings.SARVAM_API_KEY)} (len={len(settings.SARVAM_API_KEY or '')})")
    
    # Test 1: Test with model 'sarvam-105b-conversations' (current Assistant model)
    print("\n--- TEST 1: model='sarvam-105b-conversations' ---")
    payload1 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res1 = await client.post(url, headers=headers, json=payload1)
            print(f"Status: {res1.status_code}")
            print(f"Response Body: {res1.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Test with model 'sarvam-105b'
    print("\n--- TEST 2: model='sarvam-105b' ---")
    payload2 = {
        "model": "sarvam-105b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res2 = await client.post(url, headers=headers, json=payload2)
            print(f"Status: {res2.status_code}")
            print(f"Response Body: {res2.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Test with model 'sarvam-2b' or other supported models
    print("\n--- TEST 3: model='sarvam-2b' ---")
    payload3 = {
        "model": "sarvam-2b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res3 = await client.post(url, headers=headers, json=payload3)
            print(f"Status: {res3.status_code}")
            print(f"Response Body: {res3.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sarvam())
