import json

benchmarks = json.load(open('app/data/curated/benchmarks/financial_benchmarks.json', encoding='utf-8'))
for b in benchmarks:
    bid = b.get('business_node_id')
    capex = b.get('capex', {})
    keys = [k for k in capex.keys() if k not in ('fixed_cost_ratio', 'typical', 'range_min', 'range_max', 'confidence')]
    print(f"{bid:22}: {keys} (sum={sum(capex[k] for k in keys if isinstance(capex[k], (int, float)))})")
