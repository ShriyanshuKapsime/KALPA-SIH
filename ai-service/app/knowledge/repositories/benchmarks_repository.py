import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import FinancialBenchmarkSchema, MarketBenchmarkSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class BenchmarksRepository:
    """
    Repository for financial and market benchmarks across rural enterprise categories.
    """

    def __init__(
        self,
        financial_file: Optional[str] = None,
        market_file: Optional[str] = None,
    ):
        self.financial_file = financial_file or os.path.join(CURATED_DATA_DIR, "benchmarks", "financial_benchmarks.json")
        self.market_file = market_file or os.path.join(CURATED_DATA_DIR, "benchmarks", "market_benchmarks.json")
        self._financial_benchmarks: List[Dict[str, Any]] = []
        self._market_benchmarks: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.financial_file):
                with open(self.financial_file, "r", encoding="utf-8") as f:
                    self._financial_benchmarks = json.load(f)
                logger.info(f"Loaded {len(self._financial_benchmarks)} financial benchmarks")
            else:
                logger.warning(f"Financial benchmarks file not found: {self.financial_file}")
                self._financial_benchmarks = []
        except Exception as e:
            logger.error(f"Failed to load financial benchmarks: {e}")
            self._financial_benchmarks = []

        try:
            if os.path.exists(self.market_file):
                with open(self.market_file, "r", encoding="utf-8") as f:
                    self._market_benchmarks = json.load(f)
                logger.info(f"Loaded {len(self._market_benchmarks)} market benchmarks")
            else:
                logger.warning(f"Market benchmarks file not found: {self.market_file}")
                self._market_benchmarks = []
        except Exception as e:
            logger.error(f"Failed to load market benchmarks: {e}")
            self._market_benchmarks = []

    def _matches_identifier(self, item: Dict[str, Any], query_id: str) -> bool:
        q = query_id.strip().lower()
        node_id = str(item.get("business_node_id", "")).strip().lower()
        if node_id == q:
            return True
        if node_id.replace("ont_", "") == q.replace("ont_", ""):
            return True
        aliases = [str(a).strip().lower() for a in item.get("aliases", [])]
        if q in aliases:
            return True
        if q.replace("ont_", "") in [a.replace("ont_", "") for a in aliases]:
            return True
        return False

    def get_financial_benchmark(self, business_node_id: str) -> Optional[FinancialBenchmarkSchema]:
        for b in self._financial_benchmarks:
            if self._matches_identifier(b, business_node_id):
                return FinancialBenchmarkSchema(**b)
        return None

    def get_financial_benchmark_by_nic(self, nic_code: str) -> Optional[FinancialBenchmarkSchema]:
        q_nic = str(nic_code).strip()
        for b in self._financial_benchmarks:
            nic = str(b.get("nic_code", "")).strip()
            if nic and (nic == q_nic or nic.startswith(q_nic[:4]) or q_nic.startswith(nic[:4])):
                return FinancialBenchmarkSchema(**b)
        return None

    def get_all_financial_benchmarks(self) -> List[FinancialBenchmarkSchema]:
        return [FinancialBenchmarkSchema(**b) for b in self._financial_benchmarks]

    def get_market_benchmark(self, business_node_id: str) -> Optional[MarketBenchmarkSchema]:
        for b in self._market_benchmarks:
            if self._matches_identifier(b, business_node_id):
                return MarketBenchmarkSchema(**b)
        return None

    def get_all_market_benchmarks(self) -> List[MarketBenchmarkSchema]:
        return [MarketBenchmarkSchema(**b) for b in self._market_benchmarks]
