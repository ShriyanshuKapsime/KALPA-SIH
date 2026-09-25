import asyncio
import httpx
import json
from app.core.config import settings

async def test_assistant_cases():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }

    # Case 1: Standard valid payload with realistic prompt
    system_prompt = "You are KALPA, the personal AI business advisor. Financial Context: Project Cost ₹5,00,000, Bank Loan ₹4,50,000, EMI ₹7,417.43, DSCR 12.09."
    user_msg = "What is my EMI and loan amount?"
    
    payload1 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    
    print("--- CASE 1: Standard Assistant Request ---")
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload1)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"][:200]
            print("Response:", content.encode('ascii', 'backslashreplace').decode('ascii'))
        else:
            print("Error body:", res.text)

    # Case 2: History with empty message
    print("\n--- CASE 2: Empty content in message ---")
    payload2 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload2)
        print(f"Status: {res.status_code}")
        print("Body:", res.text)

    # Case 3: None content in message
    print("\n--- CASE 3: None content in message ---")
    payload3 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": None},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload3)
        print(f"Status: {res.status_code}")
        print("Body:", res.text)

    # Case 4: Invalid role name
    print("\n--- CASE 4: Invalid role ---")
    payload4 = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "bot", "content": "hello"}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload4)
        print(f"Status: {res.status_code}")
        print("Body:", res.text)

if __name__ == "__main__":
    asyncio.run(test_assistant_cases())
