"""
Milestone 2: Deterministic CapEx Intelligence & Decomposition Engine.
Decomposes fixed capital / CapEx into auditable categories:
- premises / setup
- machinery / equipment
- furniture / fixtures
- tools / workwear
- technology / POS
- vehicles (where applicable)
- other fixed assets

Strict Priority:
USER_INPUT > VERIFIED_EVIDENCE / MARKET > BENCHMARK > SUPPORTED_DERIVATION > UNKNOWN

Rules:
- NO hardcoded 70% CapEx fallback.
- NO hardcoded archetype percentage splits.
- If benchmark provides only total CapEx, preserve the total and leave category decomposition UNKNOWN (None).
- Decompose categories ONLY when explicit benchmark/user evidence exists.
- Never label a value BENCHMARKED unless an actual verified benchmark source supports it.
- Zero LLM calculations.
"""
import logging
from typing import Dict, Any, Optional, Union
from app.schemas.financial_analysis import CapExDecomposition
from app.services.financial_engine.intelligence.archetype_registry import FinancialArchetype
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData

logger = logging.getLogger(__name__)


class CapExEngine:
    """
    Deterministic Fixed Capital / CapEx decomposition engine.
    """

    def decompose(
        self,
        archetype: FinancialArchetype,
        benchmark_data: Optional[Union[BenchmarkFinancialData, Dict[str, Any]]] = None,
        capex_override: Optional[float] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        total_project_cost: Optional[float] = None,
    ) -> CapExDecomposition:
        """
        Determines CapEx and decomposes into categories when evidence exists.
        Leaves categories as None/UNKNOWN if no breakdown evidence is present.
        """
        user_inputs = user_inputs or {}

        effective_capex: Optional[float] = None
        source = "UNKNOWN"
        confidence = 0.0

        # ---------------------------------------------------------------------
        # 1. CapEx Total Determination (Strict Priority)
        # ---------------------------------------------------------------------
        # Priority 1: User explicit capex override
        if capex_override is not None and capex_override > 0:
            effective_capex = round(float(capex_override), 2)
            source = "USER_SPECIFIED"
            confidence = 1.0
        elif user_inputs.get("capex_override") is not None and float(user_inputs["capex_override"]) > 0:
            effective_capex = round(float(user_inputs["capex_override"]), 2)
            source = "USER_SPECIFIED"
            confidence = 1.0
        # Priority 2: User itemized fixed assets if provided
        elif any(user_inputs.get(k) is not None for k in ("machinery_cost", "premises_cost", "equipment_cost")):
            m = float(user_inputs.get("machinery_cost") or user_inputs.get("equipment_cost") or 0.0)
            p = float(user_inputs.get("premises_cost") or 0.0)
            f = float(user_inputs.get("furniture_cost") or 0.0)
            t = float(user_inputs.get("tools_cost") or 0.0)
            itemized_sum = m + p + f + t
            if itemized_sum > 0:
                effective_capex = round(itemized_sum, 2)
                source = "USER_SPECIFIED"
                confidence = 0.95
        # Priority 3: Benchmark typical capex
        bm_capex = None
        bm_conf = 0.90
        if benchmark_data:
            if hasattr(benchmark_data, "typical_capex_inr") and benchmark_data.typical_capex_inr is not None:
                bm_capex = float(benchmark_data.typical_capex_inr)
                bm_conf = getattr(benchmark_data, "confidence", 0.90)
            elif isinstance(benchmark_data, dict):
                bm_conf = float(benchmark_data.get("confidence", 0.90))
                if benchmark_data.get("typical_capex_inr") is not None:
                    bm_capex = float(benchmark_data["typical_capex_inr"])
                elif isinstance(benchmark_data.get("capex"), dict) and benchmark_data["capex"].get("typical") is not None:
                    bm_capex = float(benchmark_data["capex"]["typical"])

        if effective_capex is None and bm_capex is not None:
            effective_capex = round(bm_capex, 2)
            source = "BENCHMARK_DERIVED"
            confidence = bm_conf
        # Priority 4: Benchmark capex percentage applied to total project cost (ONLY if benchmark provides capex_percentage)
        elif effective_capex is None and benchmark_data and total_project_cost and total_project_cost > 0:
            capex_pct = None
            if hasattr(benchmark_data, "capex_percentage") and benchmark_data.capex_percentage is not None:
                capex_pct = float(benchmark_data.capex_percentage)
            elif isinstance(benchmark_data, dict) and benchmark_data.get("capex_percentage") is not None:
                capex_pct = float(benchmark_data["capex_percentage"])

            if capex_pct is not None:
                effective_capex = round(total_project_cost * (capex_pct / 100.0), 2)
                source = "BENCHMARK_DERIVED"
                confidence = round(bm_conf * 0.90, 2)

        if effective_capex is None or effective_capex <= 0:
            return CapExDecomposition(
                source="UNKNOWN",
                confidence=0.0,
                total_capex=None
            )

        # ---------------------------------------------------------------------
        # 2. Category Decomposition
        # Decompose categories ONLY when explicit benchmark/user evidence exists.
        # If benchmark provides only total CapEx, preserve total and leave categories None!
        # ---------------------------------------------------------------------
        raw_bm_data = benchmark_data if isinstance(benchmark_data, dict) else (
            benchmark_data.model_dump() if benchmark_data and hasattr(benchmark_data, "model_dump") else {}
        )
        bm_capex = raw_bm_data.get("capex", {}) if isinstance(raw_bm_data, dict) else {}

        # Check for user itemized inputs
        user_mach = user_inputs.get("machinery_cost") or user_inputs.get("equipment_cost")
        user_prem = user_inputs.get("premises_cost")
        user_furn = user_inputs.get("furniture_cost")
        user_tools = user_inputs.get("tools_cost")

        if any(v is not None for v in (user_mach, user_prem, user_furn, user_tools)):
            return CapExDecomposition(
                premises_setup=round(float(user_prem), 2) if user_prem is not None else None,
                machinery_equipment=round(float(user_mach), 2) if user_mach is not None else None,
                furniture_fixtures=round(float(user_furn), 2) if user_furn is not None else None,
                tools_workwear=round(float(user_tools), 2) if user_tools is not None else None,
                technology_pos=None,
                vehicles=None,
                other_fixed_assets=None,
                total_capex=effective_capex,
                source="USER_SPECIFIED",
                confidence=confidence
            )

        # Check for explicit benchmark subcategory percentages across all benchmark keys
        machinery_pct = 0.0
        premises_pct = 0.0
        furniture_pct = 0.0
        tech_pct = 0.0
        tools_pct = 0.0
        vehicles_pct = 0.0
        other_pct = 0.0

        all_cats = dict(bm_capex)
        if hasattr(benchmark_data, "capex_categories") and benchmark_data.capex_categories:
            all_cats.update(benchmark_data.capex_categories)

        for k, v in all_cats.items():
            if not isinstance(v, (int, float)) or v <= 0:
                continue
            kl = k.lower()
            if kl in ("fixed_cost_ratio", "typical", "range_min", "range_max", "confidence"):
                continue
            
            pct_val = v * 100.0 if (kl.endswith("_ratio") and v <= 1.0) else float(v)

            # Premises / Interior / Setup / Shed / Civil
            if any(term in kl for term in ("interior", "lighting", "premises", "setup", "renovation", "civil", "trial_room", "display", "shed", "fitout", "curtain")):
                premises_pct += pct_val
            # Machinery / Equipment / AC / CCTV / Specialized Tools / Mill
            elif any(term in kl for term in ("equipment", "machinery", "ac_and_cctv", "cctv", "refrigerat", "plant", "chilling", "mill", "sewing", "cutting", "ironing", "steamer", "dryer", "soldering", "multimeter", "microscope", "saw", "planer", "router", "loom", "wheel", "pottery")):
                machinery_pct += pct_val
            # Furniture / Fixtures / Racks / Chairs / Mirrors
            elif any(term in kl for term in ("furniture", "fixture", "rack", "hangers", "shelv", "counter", "mannequin", "chair", "mirror", "decor")):
                furniture_pct += pct_val
            # Technology / POS / Signage / Billing / Scale / Dongles
            elif any(term in kl for term in ("pos", "signage", "billing", "technology", "signboard", "software", "computer", "scale", "dongle")):
                tech_pct += pct_val
            # Vehicles
            elif any(term in kl for term in ("vehicle", "van", "auto", "bike", "truck")):
                vehicles_pct += pct_val
            # Tools & Workwear / Hand tools / Clamps
            elif any(term in kl for term in ("tools", "workwear", "implements", "utensils", "toolkit", "clamp", "feeder", "drinker")):
                tools_pct += pct_val
            else:
                other_pct += pct_val

        has_bm_breakdown = (premises_pct + machinery_pct + furniture_pct + tech_pct + tools_pct + vehicles_pct + other_pct) > 0

        if has_bm_breakdown:
            return CapExDecomposition(
                premises_setup=round(effective_capex * (premises_pct / 100.0), 2) if premises_pct > 0 else None,
                machinery_equipment=round(effective_capex * (machinery_pct / 100.0), 2) if machinery_pct > 0 else None,
                furniture_fixtures=round(effective_capex * (furniture_pct / 100.0), 2) if furniture_pct > 0 else None,
                tools_workwear=round(effective_capex * (tools_pct / 100.0), 2) if tools_pct > 0 else None,
                technology_pos=round(effective_capex * (tech_pct / 100.0), 2) if tech_pct > 0 else None,
                vehicles=round(effective_capex * (vehicles_pct / 100.0), 2) if vehicles_pct > 0 else None,
                other_fixed_assets=round(effective_capex * (other_pct / 100.0), 2) if other_pct > 0 else None,
                total_capex=effective_capex,
                source=source,
                confidence=confidence
            )

        # When benchmark has NO category breakdown, preserve total CapEx and leave categories None (UNKNOWN)
        return CapExDecomposition(
            premises_setup=None,
            machinery_equipment=None,
            furniture_fixtures=None,
            tools_workwear=None,
            technology_pos=None,
            vehicles=None,
            other_fixed_assets=None,
            total_capex=effective_capex,
            source=source,
            confidence=confidence
        )


# Global singleton
capex_engine = CapExEngine()
