"""
Adapters for Stage 11 Risk Engine:
Normalizes heterogeneous upstream outputs from Stage 6 (Market Intelligence), Stage 8 (Opportunity Evaluation),
Stage 9 (Financial Engine), and Stage 10 (Entrepreneur Profile) into strictly typed, auditable risk input containers.
"""
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from app.core.logging import logger


class NormalizedMarketRiskInput(BaseModel):
    """Normalized representation of Stage 6 Spatial Market Intelligence evidence."""
    demand_score: Optional[float] = None
    demand_level: Optional[str] = None  # "HIGH", "MODERATE", "LOW", "VERY_LOW"
    competitor_count: Optional[int] = None
    competitor_density: Optional[str] = None  # "HIGH", "MODERATE", "LOW"
    market_size: Optional[Any] = None
    market_accessibility: Optional[str] = None
    seasonality: Optional[Dict[str, Any]] = None
    supply_ecosystem: Optional[Dict[str, Any]] = None
    infrastructure: Optional[List[Dict[str, Any]]] = None
    geographic_reach: Optional[str] = None
    evidence_quality: Optional[float] = None
    source: str = "STAGE_6_MARKET_INTELLIGENCE"
    has_real_evidence: bool = False


class NormalizedOpportunityRiskInput(BaseModel):
    """Normalized representation of Stage 8 Market Opportunity Evaluation output."""
    opportunity_score: Optional[float] = None
    demand_score: Optional[float] = None
    competition_opportunity: Optional[float] = None
    direct_competitors: Optional[int] = None
    infrastructure_readiness: Optional[float] = None
    supply_ecosystem: Optional[float] = None
    market_accessibility: Optional[float] = None
    market_capacity: Optional[float] = None
    confidence: Optional[float] = None
    source: str = "STAGE_8_OPPORTUNITY_EVALUATION"
    has_real_evidence: bool = False


class NormalizedFinancialRiskInput(BaseModel):
    """Normalized representation of Stage 9 Financial Engine output."""
    dscr: Optional[float] = None
    break_even_percentage: Optional[float] = None
    total_project_cost: Optional[float] = None
    promoter_contribution: Optional[float] = None
    bank_loan_requirement: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    monthly_emi: Optional[float] = None
    annual_revenue: Optional[float] = None
    net_profit: Optional[float] = None
    applicable_scheme: Optional[str] = None
    source: str = "STAGE_9_FINANCIAL"
    has_real_evidence: bool = False


class NormalizedEntrepreneurRiskInput(BaseModel):
    """Normalized representation of Stage 10 Entrepreneur Profile readiness output."""
    readiness_score: Optional[float] = None
    readiness_level: Optional[str] = None
    skills_score: Optional[float] = None
    experience_score: Optional[float] = None
    training_score: Optional[float] = None
    resources_score: Optional[float] = None
    operations_score: Optional[float] = None
    years_of_experience: Optional[float] = None
    available_area_sqft: Optional[float] = None
    power_connection_type: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    identified_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = "STAGE_10_PROFILE"
    has_real_evidence: bool = False


class MarketRiskInputAdapter:
    """Adapts raw Stage 6 Market Intelligence responses or DB records into NormalizedMarketRiskInput."""

    @staticmethod
    def adapt(raw: Optional[Dict[str, Any]]) -> NormalizedMarketRiskInput:
        if not raw or not isinstance(raw, dict):
            return NormalizedMarketRiskInput()

        # Unpack full profile container if wrapped
        doc = raw.get("full_profile") or raw
        mkt_ev = doc.get("market_evidence") or doc.get("market_indicators") or doc

        norm = NormalizedMarketRiskInput()

        # 1. Demand indicators
        dem_items = mkt_ev.get("demand_indicators") or []
        if isinstance(dem_items, list) and len(dem_items) > 0:
            for item in dem_items:
                if isinstance(item, dict):
                    val = item.get("value")
                    if isinstance(val, (int, float)):
                        norm.demand_score = float(val)
                    elif isinstance(val, str):
                        val_up = val.upper()
                        if "HIGH" in val_up:
                            norm.demand_level = "HIGH"
                            norm.demand_score = 0.85
                        elif "MODERATE" in val_up or "MEDIUM" in val_up:
                            norm.demand_level = "MODERATE"
                            norm.demand_score = 0.55
                        elif "LOW" in val_up:
                            norm.demand_level = "LOW"
                            norm.demand_score = 0.25

        # Check explicit demand_evidence container
        dem_ev = mkt_ev.get("demand_evidence") or {}
        if isinstance(dem_ev, dict):
            if dem_ev.get("demand_level"):
                norm.demand_level = str(dem_ev["demand_level"]).upper()
            if dem_ev.get("demand_score") is not None:
                try:
                    norm.demand_score = float(dem_ev["demand_score"])
                except (ValueError, TypeError):
                    pass

        # If level is determined but score not set
        if norm.demand_level and norm.demand_score is None:
            if norm.demand_level in ["HIGH", "VERY_HIGH"]:
                norm.demand_score = 0.85
            elif norm.demand_level == "MODERATE":
                norm.demand_score = 0.55
            else:
                norm.demand_score = 0.25

        # 2. Competitors
        comps = mkt_ev.get("competitors") or {}
        if isinstance(comps, dict):
            total = comps.get("total_found")
            direct = comps.get("direct") or []
            if total is not None:
                norm.competitor_count = int(total)
            elif isinstance(direct, list):
                norm.competitor_count = len(direct)

            if norm.competitor_count is not None:
                if norm.competitor_count >= 5:
                    norm.competitor_density = "HIGH"
                elif norm.competitor_count >= 2:
                    norm.competitor_density = "MODERATE"
                else:
                    norm.competitor_density = "LOW"

        comp_ev = mkt_ev.get("competition_evidence") or {}
        if isinstance(comp_ev, dict):
            if comp_ev.get("competitor_count") is not None:
                norm.competitor_count = int(comp_ev["competitor_count"])
            elif comp_ev.get("direct_count") is not None:
                norm.competitor_count = int(comp_ev["direct_count"])

        # 3. Supply Access
        sup_items = mkt_ev.get("supply_access") or []
        if isinstance(sup_items, list) and len(sup_items) > 0:
            norm.supply_ecosystem = {
                "hubs_count": len(sup_items),
                "nearest_hub": sup_items[0] if isinstance(sup_items[0], dict) else {}
            }
        elif isinstance(mkt_ev.get("supply_chain_evidence"), dict):
            norm.supply_ecosystem = mkt_ev["supply_chain_evidence"]

        # 4. Seasonality
        season_items = mkt_ev.get("seasonality_evidence") or []
        if isinstance(season_items, list) and len(season_items) > 0:
            norm.seasonality = {
                "factors": season_items,
                "monthly_multipliers": season_items[0].get("monthly_multipliers", {}) if isinstance(season_items[0], dict) else {}
            }
        elif isinstance(mkt_ev.get("seasonality"), dict):
            norm.seasonality = mkt_ev["seasonality"]

        # 5. Infrastructure
        infra_items = mkt_ev.get("infrastructure") or []
        if isinstance(infra_items, list) and len(infra_items) > 0:
            norm.infrastructure = infra_items

        # 6. Quality & Reach
        quality_doc = doc.get("evidence_quality") or {}
        if isinstance(quality_doc, dict):
            norm.evidence_quality = quality_doc.get("overall_quality")

        loc_ctx = doc.get("location_context") or {}
        if isinstance(loc_ctx, dict):
            norm.geographic_reach = loc_ctx.get("target_geographic_precision") or loc_ctx.get("geographic_precision")

        # Mark real evidence presence
        norm.has_real_evidence = bool(
            norm.demand_score is not None or
            norm.demand_level is not None or
            norm.competitor_count is not None or
            norm.supply_ecosystem or
            norm.seasonality or
            norm.infrastructure
        )
        return norm


class OpportunityRiskInputAdapter:
    """Adapts raw Stage 8 Opportunity Evaluation responses or DB records into NormalizedOpportunityRiskInput."""

    @staticmethod
    def adapt(raw: Optional[Dict[str, Any]]) -> NormalizedOpportunityRiskInput:
        if not raw or not isinstance(raw, dict):
            return NormalizedOpportunityRiskInput()

        opp_res = raw.get("opportunity_result") or raw
        norm = NormalizedOpportunityRiskInput()

        # Opportunity Score
        opp_val = (
            opp_res.get("market_opportunity_score")
            if opp_res.get("market_opportunity_score") is not None
            else (
                opp_res.get("composite_opportunity_score")
                if opp_res.get("composite_opportunity_score") is not None
                else (
                    opp_res.get("opportunity_score")
                    if opp_res.get("opportunity_score") is not None
                    else (
                        raw.get("market_opportunity_score")
                        if raw.get("market_opportunity_score") is not None
                        else (
                            raw.get("composite_opportunity_score")
                            if raw.get("composite_opportunity_score") is not None
                            else raw.get("opportunity_score")
                        )
                    )
                )
            )
        )
        if opp_val is not None:
            try:
                v = float(opp_val)
                norm.opportunity_score = v / 100.0 if v > 1.0 else v
            except (ValueError, TypeError):
                pass

        # Component scores
        comp_scores = opp_res.get("component_scores") or {}
        if isinstance(comp_scores, dict):
            # Demand
            dem_detail = comp_scores.get("demand") or {}
            if isinstance(dem_detail, dict) and dem_detail.get("score") is not None:
                norm.demand_score = float(dem_detail["score"])

            # Competition
            comp_detail = comp_scores.get("competition_opportunity") or {}
            if isinstance(comp_detail, dict):
                if comp_detail.get("score") is not None:
                    norm.competition_opportunity = float(comp_detail["score"])
                if comp_detail.get("direct_competitors") is not None:
                    norm.direct_competitors = int(comp_detail["direct_competitors"])

            # Infrastructure
            infra_detail = comp_scores.get("infrastructure") or {}
            if isinstance(infra_detail, dict) and infra_detail.get("score") is not None:
                norm.infrastructure_readiness = float(infra_detail["score"])

            # Supply
            sup_detail = comp_scores.get("supply_ecosystem") or {}
            if isinstance(sup_detail, dict) and sup_detail.get("score") is not None:
                norm.supply_ecosystem = float(sup_detail["score"])

            # Market Access
            acc_detail = comp_scores.get("market_access") or {}
            if isinstance(acc_detail, dict) and acc_detail.get("score") is not None:
                norm.market_accessibility = float(acc_detail["score"])

            # Market Capacity
            cap_detail = comp_scores.get("market_capacity") or {}
            if isinstance(cap_detail, dict) and cap_detail.get("score") is not None:
                norm.market_capacity = float(cap_detail["score"])

        # Confidence
        if opp_res.get("confidence") is not None:
            norm.confidence = float(opp_res["confidence"])
        elif raw.get("evidence_quality", {}).get("overall_confidence") is not None:
            norm.confidence = float(raw["evidence_quality"]["overall_confidence"])

        norm.has_real_evidence = bool(
            norm.opportunity_score is not None or
            norm.demand_score is not None or
            norm.competition_opportunity is not None or
            norm.infrastructure_readiness is not None
        )
        return norm


class FinancialRiskInputAdapter:
    """Adapts raw Stage 9 Financial Engine outputs or FinancialProfile DB records into NormalizedFinancialRiskInput."""

    @staticmethod
    def adapt(raw: Optional[Dict[str, Any]]) -> NormalizedFinancialRiskInput:
        if not raw or not isinstance(raw, dict):
            return NormalizedFinancialRiskInput()

        norm = NormalizedFinancialRiskInput()

        # 1. DSCR
        debt_svc = raw.get("debt_service") or raw.get("financial_viability") or {}
        if isinstance(debt_svc, dict):
            dscr_val = debt_svc.get("dscr") or debt_svc.get("debt_service_coverage_ratio") or debt_svc.get("average_dscr")
            if dscr_val is not None:
                try:
                    norm.dscr = float(dscr_val)
                except (ValueError, TypeError):
                    pass
        elif raw.get("debt_service_coverage_ratio") is not None:
            norm.dscr = float(raw["debt_service_coverage_ratio"])
        elif raw.get("dscr") is not None:
            norm.dscr = float(raw["dscr"])

        # 2. Break-even
        be_doc = raw.get("break_even") or {}
        if isinstance(be_doc, dict):
            be_val = be_doc.get("break_even_point_percentage") or be_doc.get("break_even_percentage")
            if be_val is not None:
                try:
                    norm.break_even_percentage = float(be_val)
                except (ValueError, TypeError):
                    pass
        elif raw.get("break_even_percentage") is not None:
            norm.break_even_percentage = float(raw["break_even_percentage"])

        # 3. Project Financing
        fin_doc = raw.get("project_financing") or {}
        if isinstance(fin_doc, dict):
            if fin_doc.get("total_project_cost") is not None:
                norm.total_project_cost = float(fin_doc["total_project_cost"])
            if fin_doc.get("promoter_contribution") is not None:
                norm.promoter_contribution = float(fin_doc["promoter_contribution"])
            if fin_doc.get("estimated_financeable_loan") is not None:
                norm.bank_loan_requirement = float(fin_doc["estimated_financeable_loan"])
        else:
            if raw.get("total_project_cost") is not None:
                norm.total_project_cost = float(raw["total_project_cost"])
            if raw.get("promoter_contribution") is not None:
                norm.promoter_contribution = float(raw["promoter_contribution"])
            if raw.get("bank_loan_requirement") is not None:
                norm.bank_loan_requirement = float(raw["bank_loan_requirement"])

        # 4. Projections & EMI
        if raw.get("monthly_emi") is not None:
            norm.monthly_emi = float(raw["monthly_emi"])
        if raw.get("applicable_scheme_name"):
            norm.applicable_scheme = str(raw["applicable_scheme_name"])

        norm.has_real_evidence = bool(
            norm.dscr is not None or
            norm.break_even_percentage is not None or
            norm.total_project_cost is not None
        )
        return norm


class EntrepreneurProfileRiskInputAdapter:
    """Adapts raw Stage 10 Entrepreneur Profile readiness output into NormalizedEntrepreneurRiskInput."""

    @staticmethod
    def adapt(raw: Optional[Dict[str, Any]]) -> NormalizedEntrepreneurRiskInput:
        if not raw or not isinstance(raw, dict):
            return NormalizedEntrepreneurRiskInput()

        norm = NormalizedEntrepreneurRiskInput()

        # Score & level
        if raw.get("readiness_score") is not None:
            norm.readiness_score = float(raw["readiness_score"])
        if raw.get("readiness_level"):
            norm.readiness_level = str(raw["readiness_level"])

        def _get_score_val(obj):
            if obj is None:
                return None
            if isinstance(obj, (int, float)):
                return float(obj)
            if isinstance(obj, dict):
                v = obj.get("score")
                return float(v) if v is not None else None
            if hasattr(obj, "score"):
                return float(obj.score)
            return None

        # Component scores
        scores = raw.get("component_scores") or {}
        if isinstance(scores, dict):
            if scores.get("skills") is not None:
                norm.skills_score = _get_score_val(scores["skills"])
            if scores.get("experience") is not None:
                norm.experience_score = _get_score_val(scores["experience"])
            if scores.get("training") is not None:
                norm.training_score = _get_score_val(scores["training"])
            if scores.get("resources") is not None:
                norm.resources_score = _get_score_val(scores["resources"])
            if scores.get("operational") is not None:
                norm.operations_score = _get_score_val(scores["operational"])
            elif scores.get("operational_readiness") is not None:
                norm.operations_score = _get_score_val(scores["operational_readiness"])

        # Unpack user profile specifics
        ep = raw.get("entrepreneur_profile") or raw.get("user_profile") or raw
        if isinstance(ep, dict):
            exp = ep.get("experience") or {}
            if isinstance(exp, dict) and exp.get("years_of_experience") is not None:
                norm.years_of_experience = float(exp["years_of_experience"])
            elif isinstance(exp, (int, float)):
                norm.years_of_experience = float(exp)

            res = ep.get("resources") or {}
            if isinstance(res, dict):
                if res.get("available_area_sqft") is not None:
                    norm.available_area_sqft = float(res["available_area_sqft"])
                if res.get("power_connection_type"):
                    norm.power_connection_type = str(res["power_connection_type"])

            if raw.get("missing_fields"):
                norm.missing_fields = list(raw["missing_fields"])

            if raw.get("gaps"):
                norm.identified_gaps = [g if isinstance(g, dict) else (g.model_dump() if hasattr(g, "model_dump") else str(g)) for g in raw["gaps"]]

        norm.has_real_evidence = bool(
            norm.readiness_score is not None or
            norm.years_of_experience is not None or
            norm.available_area_sqft is not None or
            norm.skills_score is not None
        )
        return norm
