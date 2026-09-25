import json

bs = json.load(open('app/data/curated/benchmarks/financial_benchmarks.json', encoding='utf-8'))
for b in bs:
    bid = b.get('business_node_id')
    wc = b.get('working_capital', {})
    proj = b.get('project_cost_range', {})
    print(f"=== {bid} ===")
    print(f"  project_cost_range: {proj}")
    print(f"  working_capital: {wc}")
    print(f"  capex keys: {list(b.get('capex_breakdown_typical_pct', {}).keys())}")
