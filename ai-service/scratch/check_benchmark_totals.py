import json

benchmarks = json.load(open('app/data/curated/benchmarks/financial_benchmarks.json', encoding='utf-8'))
for b in benchmarks:
    bid = b.get('business_node_id')
    cx = b.get('capex', {}).get('typical')
    wc = b.get('working_capital', {})
    typ_m = wc.get('typical_monthly_requirement', 0)
    months = wc.get('working_capital_months_recommended', 0)
    tot_wc = typ_m * months
    tot_proj = (cx or 0) + tot_wc
    print(f"{bid:22}: CapEx={cx:10,.0f} | MonthlyWC={typ_m:8,.0f} x {months:3.1f}mo = {tot_wc:8,.0f} | TotalProj={tot_proj:10,.0f}")
