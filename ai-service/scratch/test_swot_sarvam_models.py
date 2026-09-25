import asyncio
import time
import json
import httpx
from app.core.config import settings
from app.services.swot_engine.prompt_builder import build_swot_system_prompt, build_swot_user_prompt

async def test_swot_models():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }
    
    evidence_ctx = {
        "business": {"name": "Saree Retail", "category": "Textiles", "location": "Varanasi, UP"},
        "market": {"demand": "HIGH", "competition": "MODERATE", "score": 85},
        "finance": {"dscr": 12.09, "project_cost": 500000.0, "loan_requirement": 450000.0, "break_even_pct": 14.5, "score": 88},
        "entrepreneur": {"score": 80, "skills": ["Direct Sales", "Sourcing"], "experience": ["3 years retail"]},
        "risk": {"composite_risk": "LOW-MODERATE", "top_risk_vectors": ["Seasonal Demand", "Wholesale Volatility"]},
        "feasibility": {"viability": "VIABLE", "score": 84}
    }
    
    sys_prompt = build_swot_system_prompt()
    user_prompt = build_swot_user_prompt(evidence_ctx)
    
    # Test A: sarvam-105b-conversations
    print("\n--- TEST A: model='sarvam-105b-conversations' with JSON format ---")
    payload_a = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"}
    }
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res_a = await client.post(url, headers=headers, json=payload_a)
            el_a = time.time() - t0
            print(f"Status: {res_a.status_code}, Elapsed: {el_a:.2f}s")
            print(f"Body: {res_a.text[:400]}")
    except Exception as e:
        print(f"Error: {e}")

    # Test B: sarvam-105b
    print("\n--- TEST B: model='sarvam-105b' with JSON format ---")
    payload_b = {
        "model": "sarvam-105b",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"}
    }
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res_b = await client.post(url, headers=headers, json=payload_b)
            el_b = time.time() - t0
            print(f"Status: {res_b.status_code}, Elapsed: {el_b:.2f}s")
            print(f"Body: {res_b.text[:400]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_swot_models())
