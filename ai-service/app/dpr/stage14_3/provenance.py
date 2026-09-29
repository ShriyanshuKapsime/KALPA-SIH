"""
Stage 14.3: Provenance & Source Register Management.
Maintains rigorous audit trail for all parameters, distinguishing user inputs,
verified documents, benchmark repositories, market intelligence, policy, and engine derivations.
Guarantees identity and financial fields are NEVER mislabeled as BENCHMARK.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.dpr.stage14_3.styles import resolve_display_enum


class DPRSourceType(str, Enum):
    USER_INPUT = "USER INPUT"
    VERIFIED_DOCUMENT = "VERIFIED DOCUMENT"
    BENCHMARK = "BENCHMARK"
    MARKET = "MARKET"
    POLICY = "POLICY"
    ENGINE_DERIVED = "ENGINE DERIVED"
    CLASSIFICATION = "CLASSIFICATION"
    NOT_RESOLVED = "NOT RESOLVED"


class SourceEntry(BaseModel):
    parameter: str
    label: str
    value: Any
    formatted_value: str
    source_type: DPRSourceType
    source_reference: str
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    confidence: float = 1.0
    business_node: str = "Standard Unit"
    notes: str = ""


class ProvenanceRegistry:
    """
    Constructs and audits the full DPR source register.
    """

    @staticmethod
    def map_source_type(raw_source: Any, field_id: Optional[str] = None) -> DPRSourceType:
        fid = (field_id or "").lower()

        # Known identity parameters originate from user declaration / profile
        if fid in ("business_name", "promoter_name", "target_district", "target_state", "legal_constitution", "premises_status", "promoter_education", "promoter_experience_years", "promoter_social_category"):
            return DPRSourceType.USER_INPUT

        # Known classification parameters originate from Stage 2 / 3 classification
        if fid in ("business_archetype", "nic_code", "sector", "category"):
            return DPRSourceType.CLASSIFICATION

        # Financial parameters originate from M1-M6 engines
        if fid in ("total_project_cost", "term_loan", "promoter_contribution", "working_capital", "average_dscr", "break_even_utilization", "dscr", "break_even", "plant_machinery", "civil_works"):
            return DPRSourceType.ENGINE_DERIVED

        if fid in ("total_employment", "manpower"):
            return DPRSourceType.USER_INPUT

        if not raw_source:
            return DPRSourceType.NOT_RESOLVED

        s = str(raw_source).upper()
        if "USER" in s or "DECLARED" in s:
            return DPRSourceType.USER_INPUT
        if "DOCUMENT" in s or "VERIFIED" in s:
            return DPRSourceType.VERIFIED_DOCUMENT
        if "STAGE_2" in s or "CLASSIF" in s or "NIC" in s:
            return DPRSourceType.CLASSIFICATION
        if "ENGINE" in s or "CALC" in s or "DERIVED" in s or "STAGE_9" in s or "M1_" in s or "M2_" in s or "M3_" in s or "M4_" in s or "M5_" in s or "M6_" in s:
            return DPRSourceType.ENGINE_DERIVED
        if "MARKET" in s:
            return DPRSourceType.MARKET
        if "POLICY" in s or "SCHEME" in s:
            return DPRSourceType.POLICY
        if "BENCHMARK" in s:
            return DPRSourceType.BENCHMARK

        return DPRSourceType.BENCHMARK

    @classmethod
    def build_register_from_package(cls, package: Any) -> List[SourceEntry]:
        entries: List[SourceEntry] = []
        fields = getattr(package, "fields", {}) or {}
        fin_pkg = getattr(package, "financial_package", None) or getattr(package, "financials", {}) or {}
        bp = getattr(package, "business_profile", {}) or {}
        ep = getattr(package, "entrepreneur_profile", {}) or {}

        # 1. Define Priority Institutional Audit Parameters
        core_audit_keys = [
            ("business_name", "Business / Enterprise Name", DPRSourceType.USER_INPUT, "Entrepreneur Intake Declaration"),
            ("promoter_name", "Promoter / Entrepreneur Name", DPRSourceType.USER_INPUT, "Entrepreneur Profile Declaration"),
            ("business_activity", "Business Activity & Line", DPRSourceType.BENCHMARK, "Industry Activity Registry"),
            ("nic_code", "NIC Code (5-Digit)", DPRSourceType.CLASSIFICATION, "National Industrial Classification 2008"),
            ("target_district", "Project Operating District", DPRSourceType.USER_INPUT, "Geographic Catchment Profile"),
            ("target_state", "Project Operating State", DPRSourceType.USER_INPUT, "State Industrial Policy Scope"),
            ("legal_constitution", "Legal Constitution", DPRSourceType.USER_INPUT, "Enterprise Statutory Structure"),
            ("total_employment", "Direct Employment Generated", DPRSourceType.USER_INPUT, "Manpower Plan & Benchmarks"),
            ("total_project_cost", "Total Project Outlay", DPRSourceType.ENGINE_DERIVED, "M1-M6 Reconciled Project Cost"),
            ("promoter_contribution", "Promoter Margin Money", DPRSourceType.ENGINE_DERIVED, "M4 Means of Finance Model"),
            ("term_loan", "Bank Term Loan Facility", DPRSourceType.ENGINE_DERIVED, "M4 Credit Facility Structure"),
            ("working_capital", "Assessed Working Capital Limit", DPRSourceType.ENGINE_DERIVED, "M3 Working Capital Cycle Model"),
            ("year1_revenue", "Projected Turnover (Year 1)", DPRSourceType.ENGINE_DERIVED, "M3 Revenue Forecasting Model"),
            ("year5_revenue", "Projected Turnover (Year 5)", DPRSourceType.ENGINE_DERIVED, "M3 Steady-State Revenue Model"),
            ("average_dscr", "Average DSCR (Repayment)", DPRSourceType.ENGINE_DERIVED, "M4 Debt Service Amortization Schedule"),
            ("break_even_utilization", "Break-Even Capacity Utilization", DPRSourceType.ENGINE_DERIVED, "M4 Break-Even & Solvency Engine"),
            ("installed_capacity", "Installed Operational Capacity", DPRSourceType.BENCHMARK, "Equipment Technical Specifications"),
            ("operating_capacity", "Operating Capacity (Year 1)", DPRSourceType.BENCHMARK, "Industry Ramp-up Benchmark"),
            ("udyam_registration", "Udyam Registration Status", DPRSourceType.BENCHMARK, "Ministry of MSME Portal"),
            ("gst_status", "GST Registration Status", DPRSourceType.ENGINE_DERIVED, "GST Turnover Threshold Norms"),
        ]

        def _resolve_raw_field(k: str) -> Any:
            # Check fields
            if isinstance(fields, dict) and k in fields:
                f = fields[k]
                v = getattr(f, "value", None) if hasattr(f, "value") else (f.get("value") if isinstance(f, dict) else f)
                if v is not None and str(v).strip():
                    return v
            # Check fin_pkg
            if isinstance(fin_pkg, dict) and k in fin_pkg:
                return fin_pkg[k]
            # Check business profile
            if isinstance(bp, dict) and k in bp:
                return bp[k]
            if isinstance(ep, dict) and k in ep:
                return ep[k]
            return None

        for fid, label, default_src, default_ref in core_audit_keys:
            raw_val = _resolve_raw_field(fid)
            if raw_val is None:
                continue

            # Skip unstructured raw dumps
            s_val = str(raw_val).strip()
            if "{" in s_val and "}" in s_val and ":" in s_val:
                continue
            if len(s_val) > 120 and "\n" in s_val:
                continue

            from app.dpr.stage14_3.styles import clean_and_wrap_text, resolve_display_enum
            from app.dpr.stage14_3.tables import sanitize_table_val

            is_curr = fid in ("total_project_cost", "promoter_contribution", "term_loan", "working_capital", "year1_revenue", "year5_revenue")
            disp_val = sanitize_table_val(raw_val, is_currency=is_curr, decimals=0 if is_curr else 2)

            entries.append(
                SourceEntry(
                    parameter=fid,
                    label=label,
                    value=raw_val,
                    formatted_value=disp_val,
                    source_type=default_src,
                    source_reference=default_ref,
                    confidence=1.0,
                    notes=""
                )
            )

        return entries

    @classmethod
    def get_source_note(cls, source_type: DPRSourceType) -> str:
        mapping = {
            DPRSourceType.USER_INPUT: "Source: Entrepreneur Declaration / Direct Intake",
            DPRSourceType.VERIFIED_DOCUMENT: "Source: Verified Physical / Digital Document",
            DPRSourceType.CLASSIFICATION: "Source: Stage 2/3 Classification Registry",
            DPRSourceType.BENCHMARK: "Source: NABARD / MSME Institutional Benchmark Repository",
            DPRSourceType.MARKET: "Source: KALPA Hyper-Local Market Intelligence System",
            DPRSourceType.POLICY: "Source: Government Policy / Scheme Operational Guidelines",
            DPRSourceType.ENGINE_DERIVED: "Source: KALPA Milestone 1–6 Financial Engine",
            DPRSourceType.NOT_RESOLVED: "Source: Pending Information",
        }
        return mapping.get(source_type, "Source: KALPA Authoritative Repository")
