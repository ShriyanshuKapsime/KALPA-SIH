import json
import sys
import os

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.financial_engine import financial_engine

benchmarks = json.load(open('app/data/curated/benchmarks/financial_benchmarks.json', encoding='utf-8'))
results = []
for b in benchmarks:
    bid = b['business_node_id']
    title = b.get('business_title') or b.get('business_name')
    payload = {
        'analysis_id': f'test_{bid}',
        'session_id': f'sess_{bid}',
        'business_profile': {
            'business_id': bid,
            'specific_business': title,
            'sector': b.get('aliases', [title])[0],
            'nic_code': b.get('nic_code'),
            'business_constitution': 'SOLE_PROPRIETORSHIP',
        },
        'financial_profile': {
            'available_margin_capital': 200000.0,
            'preferred_project_cost': None,
        },
        'beneficiary_profile': {
            'beneficiary_category': 'General',
            'gender': 'Male',
            'is_greenfield': True,
        },
        'location_profile': {
            'district': 'Varanasi',
            'state': 'Uttar Pradesh',
        }
    }
    try:
        resp = financial_engine.analyze(payload)
        c = resp.financial_analysis
        pkg = c.dpr_financial_package
        dc = getattr(pkg, 'data_completeness', None)
        dc_status = getattr(dc, 'status', 'NO_DC')
        unres = getattr(dc, 'unresolved_fields', [])
        tot_cost = getattr(c.project_cost_analysis, 'total_project_cost', None)
        cx = getattr(c.project_cost_analysis, 'capex', None)
        wc = getattr(c.working_capital_analysis, 'total_working_capital', None)
        rev_y1 = c.financial_projection.profit_loss_statement.years[0].revenue if (c.financial_projection and c.financial_projection.profit_loss_statement and c.financial_projection.profit_loss_statement.years) else None
        bs_bal = c.financial_projection.balance_sheet.status if (c.financial_projection and c.financial_projection.balance_sheet) else None
        cf_stat = c.financial_projection.cash_flow_statement.status if (c.financial_projection and c.financial_projection.cash_flow_statement) else None
        results.append({
            'bid': bid, 'status': 'OK', 'dc_status': str(dc_status), 'unresolved': unres,
            'cost': tot_cost, 'capex': cx, 'wc': wc, 'rev_y1': rev_y1, 'bs': bs_bal, 'cf': cf_stat
        })
    except Exception as e:
        results.append({'bid': bid, 'status': 'ERROR', 'error': str(e)})

for r in results:
    if r['status'] == 'OK':
        print(f"{r['bid']:22} Cost:{r['cost']} Cx:{r['capex']} WC:{r['wc']} Rev:{r['rev_y1']} BS:{r['bs']} DC:{r['dc_status']} Unres:{r['unresolved']}")
    else:
        print(f"{r['bid']:22} ERROR: {r['error']}")
