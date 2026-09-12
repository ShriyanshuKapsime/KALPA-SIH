import urllib.request
import json

payload = {
    "business_profile": {
        "business_profile": {
            "specific_business": "Saree & Traditional Apparel Retail",
            "normalized_concept": "saree retail",
            "sector": "Retail Trade",
            "category": "Apparel & Textiles",
            "sub_category": "Women's Ethnic Wear",
            "nic": {"code": "47711"}
        },
        "location_profile": {
            "name": "Chatra Sadar Catchment",
            "village": "Chatra",
            "block": "Chatra Sadar",
            "district": "Chatra",
            "state": "Jharkhand",
            "country": "India",
            "coordinates": {"latitude": 24.2089, "longitude": 84.8717}
        },
        "financial_profile": {
            "available_capital": 250000.0
        },
        "analysis_requirements": {
            "direct_competitors": ["Local Saree Shops", "Traditional Retailers"],
            "adjacent_competitors": ["Garment Boutiques", "Regional Wholesalers"],
            "substitute_businesses": ["Weekly Haat", "Mobile textile vendors"],
            "demand_features": ["female_population_density", "wedding_season", "festivals"],
            "infrastructure_requirements": ["PMGSY road", "power grid feeder", "commercial hub proximity"],
            "required_datasets": ["Census 2011", "MSME UDYAM", "LGD", "Mission Antyodaya"]
        }
    },
    "force_llm": False
}

req = urllib.request.Request("http://localhost:3000/api/market-intelligence/collect", method="POST")
req.add_header("Content-Type", "application/json")
data = json.dumps(payload).encode("utf-8")

with urllib.request.urlopen(req, data=data, timeout=30) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    with open("tests/sample_market_evidence_ready.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("SUCCESS: sample_market_evidence_ready.json generated.")
    print("Status:", res.get("status"))
    print("Analysis ID:", res.get("analysis_id"))
    print("Quality Score:", res.get("evidence_profile", {}).get("evidence_quality", {}).get("overall_quality"))
