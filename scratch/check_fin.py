import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "ai-service"))
import json
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
import asyncio

async def check():
    ctx = await dpr_context_builder.build_context("dairy_farm", "DPR-dairy_farm-621e4577")
    fin = ctx.get("financial_package") or {}
    print("Financial package keys:", list(fin.keys()))
    print("project_cost:", json.dumps(fin.get("project_cost"), indent=2))
    print("means_of_finance:", json.dumps(fin.get("means_of_finance"), indent=2))
    f_cost = ctx.get("fields", {}).get("cost_plant_machinery")
    print("field cost_plant_machinery in context:", f_cost)

if __name__ == "__main__":
    asyncio.run(check())
