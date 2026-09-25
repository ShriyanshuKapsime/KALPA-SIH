import sys, os
sys.path.insert(0, os.path.abspath("."))
from app.services.financial_engine.project_cost.working_capital import working_capital_engine
from app.services.financial_engine.benchmark_adapter import financial_benchmark_adapter
from app.services.financial_engine.intelligence.archetype_registry import archetype_registry, FinancialArchetype

b = financial_benchmark_adapter.get_benchmark_data('rice_mill', 'Rice Milling')
arch = archetype_registry.classify('rice_mill', 'Rice Milling')
print('archetype:', arch)
wc = working_capital_engine.analyze(arch, {}, b, {})
print('wc status:', wc.status)
print('total_wc:', wc.total_working_capital)
print('inv_req:', wc.inventory_requirement)
print('rec_req:', wc.receivable_requirement)
print('cash_buf:', wc.operating_cash_buffer)
print('pay_credit:', wc.payable_credit)
print('notes:', wc.notes)
