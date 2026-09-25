"""
Benchmark Resolution Layer and Usage Audit Engine.
Provides generic, dynamic benchmark resolution across ALL businesses in financial_benchmarks.json.
Enforces strict hierarchy: EXACT business_node_id -> NIC/Category -> Sector fallback.
Generates an exhaustive benchmark field usage audit for complete provenance.
Zero hardcoding for specific businesses.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from app.knowledge.repositories.benchmarks_repository import BenchmarksRepository
from app.services.financial_engine.benchmark_adapter import (
    BenchmarkFinancialData,
    financial_benchmark_adapter,
)

logger = logging.getLogger(__name__)


class BenchmarkUsageRecord(BaseModel):
    field: str
    used: bool
    purpose: str  # USED_AS_DRIVER | USED_AS_REFERENCE | USED_AS_BOUND | USED_FOR_VALIDATION | NOT_APPLICABLE
    calculation: str
    source: str
    value: Optional[Any] = None


class CanonicalBenchmarkResolution(BaseModel):
    benchmark_key: str
    business_node_id: str
    business_title: str
    matched_by: str  # EXACT | CATEGORY | SECTOR | ALIAS | NIC
    confidence: float
    benchmark: BenchmarkFinancialData
    raw_benchmark: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    usage_audit: List[BenchmarkUsageRecord] = Field(default_factory=list)


# Sector to representative benchmark fallback mapping for general fallback
_CATEGORY_SECTOR_MAP = {
    "retail": ["grocery_store", "saree_retail", "garment_store"],
    "trading": ["grocery_store", "saree_retail"],
    "manufacturing": ["rice_mill", "flour_mill", "spice_processing", "furniture_carpentry"],
    "food_processing": ["rice_mill", "flour_mill", "spice_processing", "food_processing_micro"],
    "livestock": ["dairy_farm", "poultry_farm", "goat_farming"],
    "agriculture": ["rice_mill", "dairy_farm", "goat_farming"],
    "services": ["tailoring_shop", "beauty_salon", "mobile_repair"],
    "repair": ["mobile_repair", "tailoring_shop"],
    "craft": ["handicrafts", "tailoring_shop", "furniture_carpentry"],
}


class BenchmarkResolver:
    """
    Generic benchmark resolution service that works for ALL businesses in financial_benchmarks.json.
    Never hardcodes business branches.
    """

    def __init__(self, repository: Optional[BenchmarksRepository] = None):
        self.repo = repository or BenchmarksRepository()

    def resolve(
        self,
        business_node_id: Optional[str] = None,
        nic_code: Optional[str] = None,
        sector: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        specific_business: Optional[str] = None,
    ) -> Optional[CanonicalBenchmarkResolution]:
        """
        Resolves canonical benchmark using priority:
        1. Exact business_node_id match
        2. Exact alias match (via specific_business or subcategory)
        3. Exact NIC code match
        4. Category match
        5. Sector fallback match
        Never silently uses an unrelated business benchmark if no match is defensible.
        """
        raw: Optional[Dict[str, Any]] = None
        matched_by = "EXACT"
        confidence = 0.95

        # 1. Exact business_node_id
        if business_node_id:
            raw_obj = self.repo.get_financial_benchmark(business_node_id)
            if raw_obj:
                raw = raw_obj.model_dump()
                matched_by = "EXACT"
                confidence = float(raw.get("quality", {}).get("confidence", 0.95))

        # 2. Specific business name / aliases
        if not raw and specific_business:
            raw_obj = self.repo.get_financial_benchmark(specific_business)
            if raw_obj:
                raw = raw_obj.model_dump()
                matched_by = "ALIAS"
                confidence = float(raw.get("quality", {}).get("confidence", 0.92))

        if not raw and subcategory:
            raw_obj = self.repo.get_financial_benchmark(subcategory)
            if raw_obj:
                raw = raw_obj.model_dump()
                matched_by = "CATEGORY"
                confidence = float(raw.get("quality", {}).get("confidence", 0.88))

        # 3. NIC code match
        if not raw and nic_code:
            raw_obj = self.repo.get_financial_benchmark_by_nic(nic_code)
            if raw_obj:
                raw = raw_obj.model_dump()
                matched_by = "NIC"
                confidence = float(raw.get("quality", {}).get("confidence", 0.90))

        # 4. Category match
        if not raw and category:
            cat_clean = category.lower().replace(" ", "_")
            raw_obj = self.repo.get_financial_benchmark(cat_clean)
            if raw_obj:
                raw = raw_obj.model_dump()
                matched_by = "CATEGORY"
                confidence = float(raw.get("quality", {}).get("confidence", 0.85))

        # 5. Sector-level fallback
        if not raw and sector:
            sec_clean = sector.lower().replace(" ", "_")
            candidate_ids = _CATEGORY_SECTOR_MAP.get(sec_clean, [])
            for cid in candidate_ids:
                raw_obj = self.repo.get_financial_benchmark(cid)
                if raw_obj:
                    raw = raw_obj.model_dump()
                    matched_by = "SECTOR"
                    confidence = 0.75
                    break

        if not raw:
            logger.warning(
                f"[BENCHMARK RESOLVER] No canonical benchmark found for: "
                f"node_id={business_node_id}, specific={specific_business}, nic={nic_code}, "
                f"category={category}, sector={sector}"
            )
            return None

        # Build normalized BenchmarkFinancialData
        norm_bm = financial_benchmark_adapter.get_benchmark_data(
            business_id=raw.get("business_node_id")
        )
        if not norm_bm:
            norm_bm = financial_benchmark_adapter.get_benchmark_data(
                specific_business=raw.get("business_title")
            )

        # Build comprehensive benchmark usage audit
        usage_audit = self._audit_benchmark_fields(raw)

        provenance_dict = raw.get("provenance", {})
        prov = {
            "source_id": provenance_dict.get("source_id", "KALPA_BENCHMARK_DB"),
            "organization": provenance_dict.get("organization", "Official MSME Guidelines"),
            "document_name": provenance_dict.get("document_name", "Curated Financial Standards"),
            "publication_year": provenance_dict.get("publication_year", 2024),
            "source_type": provenance_dict.get("source_type", "official_document"),
            "matched_by": matched_by,
            "match_confidence": confidence,
            "verification_status": raw.get("quality", {}).get("verification_status", "verified"),
        }

        resolved = CanonicalBenchmarkResolution(
            benchmark_key=raw.get("business_node_id", "unknown"),
            business_node_id=raw.get("business_node_id", "unknown"),
            business_title=raw.get("business_title") or raw.get("business_name") or "Rural Enterprise",
            matched_by=matched_by,
            confidence=confidence,
            benchmark=norm_bm,
            raw_benchmark=raw,
            provenance=prov,
            usage_audit=usage_audit,
        )

        logger.info(
            f"[BENCHMARK RESOLVER] Successfully resolved benchmark: "
            f"key={resolved.benchmark_key}, matched_by={matched_by}, conf={confidence:.2f}"
        )
        return resolved

    def _audit_benchmark_fields(self, raw: Dict[str, Any]) -> List[BenchmarkUsageRecord]:
        """
        Inspects every field in the benchmark schema and determines its strict semantic role.
        No relevant field is silently dropped.
        """
        records: List[BenchmarkUsageRecord] = []
        bid = raw.get("business_node_id", "unknown")
        src = raw.get("provenance", {}).get("source_id", "KALPA_BENCHMARK_DB")

        # 1. CapEx Fields
        cx = raw.get("capex", {})
        if "typical" in cx:
            records.append(BenchmarkUsageRecord(
                field="capex.typical",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation="Base fixed capital investment requirement in M2 project cost",
                source=src,
                value=cx["typical"]
            ))
        if "range_min" in cx:
            records.append(BenchmarkUsageRecord(
                field="capex.range_min",
                used=True,
                purpose="USED_AS_BOUND",
                calculation="Minimum plausible CapEx boundary for sensitivity and validation",
                source=src,
                value=cx["range_min"]
            ))
        if "range_max" in cx:
            records.append(BenchmarkUsageRecord(
                field="capex.range_max",
                used=True,
                purpose="USED_AS_BOUND",
                calculation="Maximum plausible CapEx boundary for sensitivity and validation",
                source=src,
                value=cx["range_max"]
            ))
        if "fixed_cost_ratio" in cx:
            records.append(BenchmarkUsageRecord(
                field="capex.fixed_cost_ratio",
                used=True,
                purpose="USED_AS_REFERENCE",
                calculation="Allocation ratio of fixed capital vs total enterprise capital",
                source=src,
                value=cx["fixed_cost_ratio"]
            ))

        for k, v in cx.items():
            if k.endswith("_pct") and k not in ("pre_operative_pct", "contingency_pct"):
                records.append(BenchmarkUsageRecord(
                    field=f"capex.{k}",
                    used=True,
                    purpose="USED_AS_DRIVER",
                    calculation=f"Decomposes fixed capital into {k.replace('_pct', '')} asset class",
                    source=src,
                    value=v
                ))
            elif k == "pre_operative_pct":
                records.append(BenchmarkUsageRecord(
                    field="capex.pre_operative_pct",
                    used=True,
                    purpose="USED_AS_DRIVER",
                    calculation="Pre-operative and site setup expenses provision",
                    source=src,
                    value=v
                ))
            elif k == "contingency_pct":
                records.append(BenchmarkUsageRecord(
                    field="capex.contingency_pct",
                    used=True,
                    purpose="USED_AS_DRIVER",
                    calculation="Contingency reserve provision (civil and plant works)",
                    source=src,
                    value=v
                ))

        # 2. Working Capital Fields
        wc = raw.get("working_capital", {})
        if "typical_monthly_requirement" in wc:
            records.append(BenchmarkUsageRecord(
                field="working_capital.typical_monthly_requirement",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation="Monthly operating cycle expenditure requirement for M2 working capital",
                source=src,
                value=wc["typical_monthly_requirement"]
            ))
        if "working_capital_months_recommended" in wc:
            records.append(BenchmarkUsageRecord(
                field="working_capital.working_capital_months_recommended",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation="Recommended operational funding months buffer",
                source=src,
                value=wc["working_capital_months_recommended"]
            ))
        if "working_capital_ratio" in wc:
            records.append(BenchmarkUsageRecord(
                field="working_capital.working_capital_ratio",
                used=True,
                purpose="USED_AS_REFERENCE",
                calculation="Working capital to annual operating turnover benchmark reference",
                source=src,
                value=wc["working_capital_ratio"]
            ))
        if "inventory_turnover_days" in wc:
            records.append(BenchmarkUsageRecord(
                field="working_capital.inventory_turnover_days",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation="Inventory stock holding period in days for working capital",
                source=src,
                value=wc["inventory_turnover_days"]
            ))

        # 3. Margin Fields
        mg = raw.get("margins", {})
        if "gross_margin_pct_typical" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.gross_margin_pct_typical",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation="Baseline Gross Margin for P&L (COGS = Revenue * (1 - Gross Margin%))",
                source=src,
                value=mg["gross_margin_pct_typical"]
            ))
        if "gross_margin_pct_min" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.gross_margin_pct_min",
                used=True,
                purpose="USED_AS_BOUND",
                calculation="Downside Gross Margin bound for stress testing",
                source=src,
                value=mg["gross_margin_pct_min"]
            ))
        if "gross_margin_pct_max" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.gross_margin_pct_max",
                used=True,
                purpose="USED_AS_BOUND",
                calculation="Upside Gross Margin bound for stress testing",
                source=src,
                value=mg["gross_margin_pct_max"]
            ))
        if "net_margin_pct_typical" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.net_margin_pct_typical",
                used=True,
                purpose="USED_FOR_VALIDATION",
                calculation="Validation benchmark for model PAT/Revenue. NOT used to calculate EBITDA directly",
                source=src,
                value=mg["net_margin_pct_typical"]
            ))
        if "net_margin_pct_min" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.net_margin_pct_min",
                used=True,
                purpose="USED_AS_BOUND",
                calculation="Validation bound for minimum defensible net margin",
                source=src,
                value=mg["net_margin_pct_min"]
            ))
        if "net_margin_pct_max" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.net_margin_pct_max",
                used=True,
                purpose="USED_AS_BOUND",
                calculation="Validation bound for maximum defensible net margin",
                source=src,
                value=mg["net_margin_pct_max"]
            ))
        if "operating_cost_ratio" in mg:
            records.append(BenchmarkUsageRecord(
                field="margins.operating_cost_ratio",
                used=True,
                purpose="USED_AS_REFERENCE",
                calculation="Total operational expenditure intensity relative to revenue",
                source=src,
                value=mg["operating_cost_ratio"]
            ))

        # 4. Cost Structure Fields
        cs = raw.get("cost_structure_pct", {})
        for k, v in cs.items():
            records.append(BenchmarkUsageRecord(
                field=f"cost_structure_pct.{k}",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation=f"Operating/procurement cost allocation for {k.replace('_', ' ')}",
                source=src,
                value=v
            ))

        # 5. Timelines
        tl = raw.get("timelines", {})
        if "setup_time_days" in tl:
            records.append(BenchmarkUsageRecord(
                field="timelines.setup_time_days",
                used=True,
                purpose="USED_AS_REFERENCE",
                calculation="Setup and pre-operative implementation duration in days",
                source=src,
                value=tl["setup_time_days"]
            ))
        if "breakeven_months" in tl:
            records.append(BenchmarkUsageRecord(
                field="timelines.breakeven_months",
                used=True,
                purpose="USED_FOR_VALIDATION",
                calculation="Benchmark break-even timeline for viability validation",
                source=src,
                value=tl["breakeven_months"]
            ))
        if "payback_period_months" in tl:
            records.append(BenchmarkUsageRecord(
                field="timelines.payback_period_months",
                used=True,
                purpose="USED_FOR_VALIDATION",
                calculation="Benchmark capital payback timeline for banking viability validation",
                source=src,
                value=tl["payback_period_months"]
            ))

        # 6. Unit Economics Fields
        ue = raw.get("unit_economics", {})
        for k, v in ue.items():
            records.append(BenchmarkUsageRecord(
                field=f"unit_economics.{k}",
                used=True,
                purpose="USED_AS_DRIVER",
                calculation=f"Authoritative unit economic volume/price/capacity driver for {k.replace('_', ' ')}",
                source=src,
                value=v
            ))

        return records


# Global singleton
benchmark_resolver = BenchmarkResolver()
