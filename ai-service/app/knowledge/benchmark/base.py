"""
Benchmark Knowledge Base Interface.
Future content:
- NABARD Unit Costs & Norms
- Investment benchmarks
- Standard cost structures & equipment pricing
- Financial benchmarks & industry reference ranges
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class NABARDBenchmarkItem(BaseModel):
    activity_code: str
    activity_name: str
    state: str
    unit_cost_inr: float
    repayment_period_years: int
    grace_period_months: int


class BenchmarkDatabaseRegistry:
    """
    Registry for NABARD and institutional unit costs and benchmarks.
    """
    def __init__(self):
        self.benchmarks: Dict[str, NABARDBenchmarkItem] = {}

    def lookup_unit_cost(self, activity_code: str) -> Optional[NABARDBenchmarkItem]:
        return self.benchmarks.get(activity_code)
