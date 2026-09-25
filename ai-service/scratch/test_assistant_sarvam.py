import asyncio
import json
import httpx
from app.core.config import settings
from app.services.assistant_engine.assistant_service import assistant_service

async def test_assistant_call():
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
    }
    
    # Create realistic context slice
    context_slice = {
        "business_profile": {
            "business_id": "saree_retail",
            "specific_business": "Saree Retail",
            "sector": "Retail",
            "category": "Textiles",
            "location": "Varanasi, UP",
            "capital": 200000.0,
            "target_scale": "micro"
        },
        "financial_context": {
            "project_cost": {"total_project_cost": 500000.0, "working_capital": 180000.0},
            "funding": {"required_promoter_contribution": 50000.0, "institutional_loan": 450000.0},
            "debt": {"emi": 7417.43, "interest_rate": 8.0, "tenure_months": 84},
            "banking_appraisal": {"average_dscr": 12.09, "break_even_utilization_pct": 14.5}
        },
        "feasibility_result": {
            "overall_feasibility_score": 84,
            "viability_status": "VIABLE",
            "recommendation": "PROCEED"
        }
    }
    
    sys_prompt = assistant_service._build_conversational_system_prompt(
        context_slice=context_slice,
        intent="REPAYMENT_QUESTION",
        biz_memory={},
        conv_memory={},
        language="en"
    )
    
    print(f"System prompt length: {len(sys_prompt)} chars")
    
    user_msg = "What will my monthly EMI be?"
    
    # Test with sarvam-105b-conversations
    payload = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    
    print("\n--- Sending request to Sarvam ---")
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

if __name__ == "__main__":
    asyncio.run(test_assistant_call())
