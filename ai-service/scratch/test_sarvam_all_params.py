import asyncio
import httpx
from app.core.config import settings

async def test_params():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }
    
    # Check 1: Extra keys in payload
    print("--- 1. Extra key 'stream: False' or unknown keys ---")
    p1 = {
        "model": "sarvam-105b-conversations",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.2,
        "max_tokens": 1200,
        "extra_field_unknown": "test"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r1 = await client.post(url, headers=headers, json=p1)
        print(f"Status: {r1.status_code}, Body: {r1.text[:300]}")

    # Check 2: response_format on conversations model
    print("\n--- 2. response_format on conversations model ---")
    p2 = {
        "model": "sarvam-105b-conversations",
        "messages": [{"role": "user", "content": "Hello"}],
        "response_format": {"type": "json_object"}
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r2 = await client.post(url, headers=headers, json=p2)
        print(f"Status: {r2.status_code}, Body: {r2.text[:300]}")

    # Check 3: temperature out of range (e.g. > 1 or negative)
    print("\n--- 3. temperature negative or invalid ---")
    p3 = {
        "model": "sarvam-105b-conversations",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": -0.5
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r3 = await client.post(url, headers=headers, json=p3)
        print(f"Status: {r3.status_code}, Body: {r3.text[:300]}")

    # Check 4: max_tokens > limit (e.g. 100000)
    print("\n--- 4. max_tokens huge ---")
    p4 = {
        "model": "sarvam-105b-conversations",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 100000
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r4 = await client.post(url, headers=headers, json=p4)
        print(f"Status: {r4.status_code}, Body: {r4.text[:300]}")

    # Check 5: role ordering or assistant as first message
    print("\n--- 5. assistant as first message ---")
    p5 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "assistant", "content": "I am here."},
            {"role": "user", "content": "Hello"}
        ]
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r5 = await client.post(url, headers=headers, json=p5)
        print(f"Status: {r5.status_code}, Body: {r5.text[:300]}")

    # Check 6: consecutive same role messages (user then user)
    print("\n--- 6. consecutive user messages ---")
    p6 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello 1"},
            {"role": "user", "content": "Hello 2"}
        ]
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r6 = await client.post(url, headers=headers, json=p6)
        print(f"Status: {r6.status_code}, Body: {r6.text[:300]}")

    # Check 7: consecutive assistant messages (assistant then assistant)
    print("\n--- 7. consecutive assistant messages ---")
    p7 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello 1"},
            {"role": "assistant", "content": "Hi 1"},
            {"role": "assistant", "content": "Hi 2"},
            {"role": "user", "content": "Hello 2"}
        ]
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r7 = await client.post(url, headers=headers, json=p7)
        print(f"Status: {r7.status_code}, Body: {r7.text[:300]}")

if __name__ == "__main__":
    asyncio.run(test_params())
