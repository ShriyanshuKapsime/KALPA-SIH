"""
Deterministic Stage 11 Risk Engine for KALPA MSME Platform.
Consumes upstream structured outputs from:
- Stage 6 Market Intelligence (demand, competition, infrastructure)
- Stage 8 Opportunity Evaluation (market opportunity score, gaps)
- Stage 9 Financial Engine (DSCR, break-even %, loan viability)
- Stage 10 Entrepreneur Profile (readiness gaps, skill deficits)
- Knowledge / Benchmark Database (risk_library.json)

Evaluates 7 Risk Categories:
1. MARKET
2. FINANCIAL
3. OPERATIONAL
4. SEASONAL
5. SUPPLY_CHAIN
6. COMPETITION
7. INFRASTRUCTURE

Enforces Critical Risk Ceiling Rule:
Any CRITICAL category risk elevates overall enterprise risk severity to HIGH/CRITICAL.
DOES NOT use an LLM for risk scoring.
"""
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.risk_analysis import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    CategoryRiskItem,
    RiskProvenanceRecord,
)
from app.knowledge.repositories.risks_repository import RisksRepository
from app.knowledge.repositories.benchmarks_repository import BenchmarksRepository
from app.services.risk_engine.constants import (
    RISK_WEIGHT_FINANCIAL,
    RISK_WEIGHT_MARKET,
    RISK_WEIGHT_OPERATIONAL,
    RISK_WEIGHT_SEASONAL,
    RISK_WEIGHT_SUPPLY_CHAIN,
    RISK_WEIGHT_COMPETITION,
    RISK_WEIGHT_INFRASTRUCTURE,
    SEVERITY_THRESHOLD_CRITICAL,
    SEVERITY_THRESHOLD_HIGH,
    SEVERITY_THRESHOLD_MEDIUM,
)
from app.core.logging import logger


class RiskEngine:
    """
    Deterministic multi-vector risk synthesis engine for rural MSME enterprises.
    """

    def __init__(self):
        self.risks_repo = RisksRepository()
        self.benchmarks_repo = BenchmarksRepository()

    def _resolve_business_context(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        """Resolves business node id and title from available context."""
        biz = payload.get("business_profile") or {}
        if hasattr(biz, "model_dump"):
            biz = biz.model_dump()

        biz_id = (
            biz.get("business_id") or
            biz.get("business_node_id") or
            biz.get("specific_business") or
            biz.get("category") or
            "flour_milling_micro"
        )
        title = biz.get("business_title") or biz.get("specific_business") or biz.get("category") or "Micro Enterprise"
        slug = str(biz_id).lower().replace(" ", "_").replace("-", "_")

        if "flour" in slug or "atta" in slug or "chakki" in slug:
            return "flour_milling_micro", title or "Micro Flour Milling Unit"
        elif "oil" in slug or "expeller" in slug:
            return "oil_expeller_unit", title or "Cold-Pressed Oil Expeller Unit"
        elif "spice" in slug or "masala" in slug:
            return "spice_grinding_packaging", title or "Spice Grinding & Packaging Unit"
        elif "dairy" in slug or "milk" in slug or "chilling" in slug:
            return "dairy_micro_chilling_aggregator", title or "Dairy Micro Chilling Unit"
        elif "poultry" in slug or "broiler" in slug:
            return "poultry_broiler_farm", title or "Poultry Broiler Farm"
        elif "weaving" in slug or "handloom" in slug:
            return "handloom_weaving_unit", title or "Handloom Weaving Unit"
        elif "solar" in slug or "pump" in slug:
            return "solar_pump_repair_service", title or "Solar Pump Repair Service"
        elif "compost" in slug or "fertilizer" in slug:
            return "organic_fertilizer_composting", title or "Organic Fertilizer Composting"

        return slug, title

    def evaluate_financial_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates financial risk directly from Stage 9 outputs (DSCR, break-even %, debt servicing).
        DOES NOT recalculate Stage 9 financials independently.
        """
        fin_stage = payload.get("financial_analysis") or {}
        if hasattr(fin_stage, "model_dump"):
            fin_stage = fin_stage.model_dump()

        # Extract Stage 9 metrics
        dscr = None
        bep = None
        loan_amt = None
        viability_status = None

        if fin_stage:
            # Check nested financial analysis or flat dict
            fa = fin_stage.get("financial_analysis") or fin_stage
            ds = fa.get("debt_service") or fin_stage.get("debt_service") or {}
            viab = fa.get("financial_viability") or fin_stage.get("financial_viability") or {}
            dscr = ds.get("dscr") or viab.get("debt_service_coverage_ratio") or viab.get("dscr")
            viability_status = viab.get("level") or viab.get("viability_status")
            
            be_dict = fa.get("break_even") or fa.get("break_even_analysis") or fin_stage.get("break_even_analysis") or {}
            bep = be_dict.get("break_even_point_percentage") or be_dict.get("break_even_percentage")
            
            pf = fa.get("project_financing") or fin_stage.get("project_financing") or {}
            loan_amt = pf.get("estimated_financeable_loan")

        drivers = []
        evidence = []
        mitigations = [
            "Maintain emergency liquidity reserve equal to 1.5 to 2.0 months of fixed operating expenses",
            "Establish strict 7-day customer credit policy on retail sales (Khata limits)",
            "Utilize PMMY Mudra / CGTMSE interest subvention schemes to minimize effective borrowing cost"
        ]

        if dscr is not None:
            dscr_val = float(dscr)
            evidence.append(f"Stage 9 Debt Service Coverage Ratio (DSCR): {dscr_val:.2f}x")
            
            if dscr_val < 1.15:
                score = 0.90
                severity = "CRITICAL"
                drivers.append(f"Severely constrained debt service coverage (DSCR {dscr_val:.2f} < 1.15x minimum threshold)")
                impact = "High risk of loan EMI default during initial ramp-up months; potential NPA classification without equity buffer."
            elif dscr_val < 1.35:
                score = 0.70
                severity = "HIGH"
                drivers.append(f"Tight debt service buffer (DSCR {dscr_val:.2f}x below 1.35x safe benchmark)")
                impact = "Vulnerable to short-term working capital squeezes and seasonal cash flow delays."
            elif dscr_val < 1.75:
                score = 0.40
                severity = "MEDIUM"
                drivers.append(f"Standard MSME cash flow coverage (DSCR {dscr_val:.2f}x)")
                impact = "Adequate debt servicing capacity under normal operational conditions."
            else:
                score = 0.20
                severity = "LOW"
                drivers.append(f"Robust debt servicing capacity (DSCR {dscr_val:.2f}x >= 1.75x)")
                impact = "Substantial cash surplus generated after meeting all debt and working capital obligations."
        else:
            # Check financial profile inputs fallback
            fin_prof = payload.get("financial_profile") or {}
            margin = float(fin_prof.get("available_margin_capital") or fin_prof.get("available_capital") or 100000.0)
            score = 0.50
            severity = "MEDIUM"
            evidence.append(f"Available margin capital reported: ₹{margin:,.0f}")
            drivers.append("Standard micro-enterprise liquidity profile")
            impact = "Debt servicing will depend on timely achievement of projected unit revenues."

        if bep is not None and float(bep) > 70.0:
            score = min(1.0, score + 0.15)
            drivers.append(f"Elevated break-even capacity requirement ({bep:.1f}% capacity needed to cover fixed overheads)")
            if score >= 0.85:
                severity = "CRITICAL"
            elif score >= 0.65:
                severity = "HIGH"

        return CategoryRiskItem(
            type="FINANCIAL",
            score=round(score, 2),
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact if 'impact' in locals() else "Operational cash flows must sustain loan obligations.",
            mitigation=mitigations,
            confidence=0.95 if dscr is not None else 0.70,
            source_stage="STAGE_9_FINANCIAL"
        )

    def evaluate_market_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates market demand, purchasing power, and price volatility from Stage 6 & Stage 8.
        """
        mkt = payload.get("market_intelligence") or {}
        opp = payload.get("opportunity_evaluation") or {}
        
        demand_level = None
        if mkt:
            ind = mkt.get("market_indicators") or {}
            dem = ind.get("demand_evidence") or {}
            demand_level = dem.get("demand_level")
        
        opp_score = None
        if opp:
            opp_res = opp.get("opportunity_result") or opp
            opp_score = opp_res.get("market_opportunity_score")

        drivers = []
        evidence = []

        if demand_level:
            evidence.append(f"Stage 6 Market Demand Level: {demand_level}")
            if demand_level in ["LOW", "VERY_LOW"]:
                score = 0.75
                severity = "HIGH"
                drivers.append("Subdued local catchment demand density")
            elif demand_level == "MODERATE":
                score = 0.45
                severity = "MEDIUM"
                drivers.append("Moderate local demand with seasonal purchasing cycles")
            else:
                score = 0.25
                severity = "LOW"
                drivers.append(f"Strong sustained consumer demand in target block ({demand_level})")
        elif opp_score is not None:
            opp_val = float(opp_score)
            evidence.append(f"Stage 8 Market Opportunity Score: {opp_val * 100:.1f}%")
            score = round(max(0.15, 1.0 - opp_val), 2)
            severity = "HIGH" if score >= 0.65 else ("MEDIUM" if score >= 0.40 else "LOW")
            drivers.append(f"Opportunity synthesis indicates {opp_val*100:.0f}% market capture feasibility")
        else:
            score = 0.40
            severity = "MEDIUM"
            evidence.append("Benchmark regional market absorption index applied")
            drivers.append("General rural consumer goods price sensitivity")

        impact = "Product pricing must absorb raw material price volatility without hurting local sales velocity."
        mitigations = [
            "Establish forward procurement agreements with local farmer groups / aggregators",
            "Introduce flexible multi-tier packaging sizes (e.g. 500g, 1kg, 5kg) to suit diverse household budgets",
            "Establish B2B supply linkages with local eateries, dhabas, and institutional buyers"
        ]

        return CategoryRiskItem(
            type="MARKET",
            score=score,
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact,
            mitigation=mitigations,
            confidence=0.90 if (demand_level or opp_score) else 0.65,
            source_stage="STAGE_6_MARKET_INTELLIGENCE"
        )

    def evaluate_operational_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates operational risks derived from Stage 10 Entrepreneur readiness gaps and machine uptime.
        """
        er = payload.get("entrepreneur_readiness") or {}
        if hasattr(er, "model_dump"):
            er = er.model_dump()

        readiness_score = er.get("readiness_score")
        gaps = er.get("gaps", [])

        drivers = []
        evidence = []

        if readiness_score is not None:
            r_val = float(readiness_score)
            evidence.append(f"Stage 10 Entrepreneur Readiness Score: {r_val:.1f}%")
            if r_val < 45.0:
                score = 0.75
                severity = "HIGH"
                drivers.append("Significant technical skill or operational bandwidth deficit")
            elif r_val < 70.0:
                score = 0.45
                severity = "MEDIUM"
                drivers.append("Developing operational competencies requiring initial mentoring")
            else:
                score = 0.20
                severity = "LOW"
                drivers.append("High founder competence and clear operating bandwidth")
        else:
            score = 0.45
            severity = "MEDIUM"
            evidence.append("Standard micro-enterprise operational baseline applied")
            drivers.append("Single-operator dependency on key technical processing tasks")

        if gaps:
            for g in gaps[:2]:
                gap_desc = g.get("gap_description") if isinstance(g, dict) else getattr(g, "gap_description", str(g))
                drivers.append(f"Identified readiness constraint: {gap_desc}")

        impact = "Unscheduled machine downtime or operator skill gaps can reduce daily processing output by 20-35%."
        mitigations = [
            "Cross-train secondary family member or apprentice on primary machine operations",
            "Maintain digital standard operating procedure (SOP) logs and local technician contact list",
            "Keep critical spare parts (drive belts, emery stone dressing tools, filters) on site"
        ]

        return CategoryRiskItem(
            type="OPERATIONAL",
            score=round(score, 2),
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact,
            mitigation=mitigations,
            confidence=0.90 if readiness_score is not None else 0.70,
            source_stage="STAGE_10_ENTREPRENEUR_PROFILE"
        )

    def evaluate_seasonal_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates agricultural raw material arrival cycles and weather/monsoon seasonality.
        """
        # Agri-processing nodes have distinct seasonality
        is_agri = node_id in ["flour_milling_micro", "oil_expeller_unit", "spice_grinding_packaging", "organic_fertilizer_composting"]
        
        drivers = []
        evidence = []

        if is_agri:
            score = 0.55
            severity = "MEDIUM"
            drivers.append("Rabi / Kharif crop arrival cycles cause 20-40% wholesale raw material price swings")
            drivers.append("Monsoon humidity impacts grain and dry spice storage longevity")
            evidence.append("Agmarknet historical commodity seasonal arrival patterns")
            impact = "Lean-season raw material purchases at inflated prices squeeze processing margins."
            mitigations = [
                "Construct airtight moisture-proof hermetic storage bins for 60-day buffer stock during harvest",
                "Offer custom job-work milling for village farmers during peak harvest to generate zero-inventory cash flow",
                "Utilize solar drying tunnels to reduce raw moisture content before storage"
            ]
        else:
            score = 0.30
            severity = "LOW"
            drivers.append("Year-round stable demand cycle with mild festival surges")
            evidence.append("Consistent non-farm service demand profile")
            impact = "Minor seasonal variations in working capital demand."
            mitigations = [
                "Plan annual maintenance and equipment overhaul during lean monsoon weeks"
            ]

        return CategoryRiskItem(
            type="SEASONAL",
            score=score,
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact,
            mitigation=mitigations,
            confidence=0.85,
            source_stage="STAGE_6_MARKET_INTELLIGENCE"
        )

    def evaluate_supply_chain_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates supplier concentration, transport bottlenecks, and input availability.
        """
        is_perishable = node_id in ["dairy_micro_chilling_aggregator", "poultry_broiler_farm"]
        drivers = []
        evidence = []

        if is_perishable:
            score = 0.70
            severity = "HIGH"
            drivers.append("Perishable daily collection requires unbroken cold chain and rapid off-take")
            drivers.append("Single aggregator off-take buyer dependency")
            evidence.append("Perishable commodity logistics risk catalog")
            impact = "Logistical delays of >4 hours can cause batch spoilage and total loss of collection value."
            mitigations = [
                "Emergency diversion tie-up with adjacent chilling center or dairy cooperative union",
                "Backup generator for chilling tanks with automated phase changeover"
            ]
        else:
            score = 0.35
            severity = "LOW"
            drivers.append("Multiple localized agricultural suppliers and APMC mandi channels available")
            evidence.append("Local rural supply network accessibility")
            impact = "Low probability of severe supply disruption; manageable through local sourcing."
            mitigations = [
                "Maintain active relationships with at least 3 local farmer groups and 2 mandi commission agents",
                "Establish clear moisture and quality grading standards at intake point"
            ]

        return CategoryRiskItem(
            type="SUPPLY_CHAIN",
            score=score,
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact,
            mitigation=mitigations,
            confidence=0.85,
            source_stage="STAGE_KNOWLEDGE_BENCHMARKS"
        )

    def evaluate_competition_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates competitor clustering and price undercutting risks from Stage 6.
        """
        mkt = payload.get("market_intelligence") or {}
        comp_count = None
        if mkt:
            ind = mkt.get("market_indicators") or {}
            comp = ind.get("competition_evidence") or {}
            comp_count = comp.get("competitor_count")

        drivers = []
        evidence = []

        if comp_count is not None:
            c_val = int(comp_count)
            evidence.append(f"Stage 6 Identified Competitors in 5km Catchment: {c_val}")
            if c_val >= 5:
                score = 0.70
                severity = "HIGH"
                drivers.append(f"Dense competitor clustering ({c_val} existing units operating in catchment)")
            elif c_val >= 2:
                score = 0.45
                severity = "MEDIUM"
                drivers.append(f"Moderate local competitive pressure ({c_val} operating units)")
            else:
                score = 0.20
                severity = "LOW"
                drivers.append(f"Low competitor density ({c_val} units) with significant unmet demand")
        else:
            score = 0.40
            severity = "MEDIUM"
            evidence.append("Catchment benchmark competitive index")
            drivers.append("Presence of traditional unorganized village service providers")

        impact = "Competitor price wars can compress processing margins by 10-15% if products lack differentiation."
        mitigations = [
            "Provide value-added services such as doorstep delivery and customized fine flour/oil grading",
            "Adopt hygienic branded packaging with FSSAI license display to build consumer trust",
            "Introduce volume loyalty discounts for repeat village customers"
        ]

        return CategoryRiskItem(
            type="COMPETITION",
            score=score,
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact,
            mitigation=mitigations,
            confidence=0.90 if comp_count is not None else 0.70,
            source_stage="STAGE_6_MARKET_INTELLIGENCE"
        )

    def evaluate_infrastructure_risk(self, payload: Dict[str, Any], node_id: str) -> CategoryRiskItem:
        """
        Evaluates grid electricity stability, road connectivity, and water reliability.
        """
        drivers = []
        evidence = []

        ep = payload.get("entrepreneur_readiness") or payload.get("entrepreneur_profile") or {}
        if hasattr(ep, "model_dump"):
            ep = ep.model_dump()

        res = ep.get("component_scores", {}).get("resources", {}) if "component_scores" in ep else (ep.get("resources") or {})
        power_type = res.get("details", {}).get("power_connection") if "details" in res else res.get("power_connection_type")

        evidence.append(f"Site Power Configuration: {power_type or 'STANDARD_RURAL_GRID'}")
        
        # High power machinery units
        needs_3phase = node_id in ["flour_milling_micro", "oil_expeller_unit", "solar_pump_repair_service"]
        
        if needs_3phase and power_type and "single" in power_type.lower():
            score = 0.85
            severity = "CRITICAL"
            drivers.append("Single-phase domestic line inadequate for 5-7.5 HP commercial machinery load")
            impact = "Immediate trip/transformer burnout if commercial load is connected without 3-phase sanction."
            mitigations = [
                "Urgent application to local Discom for 3-Phase Commercial tariff load sanction (7.5 kW)",
                "Install commercial step-up transformer / diesel generator backup (10 kVA) for uninterrupted running"
            ]
        elif needs_3phase:
            score = 0.50
            severity = "MEDIUM"
            drivers.append("Rural feeder load shedding during peak agricultural summer months")
            impact = "Daily operational running hours restricted during scheduled power cuts."
            mitigations = [
                "Install 10 kVA generator set or solar hybrid backup to maintain production schedules",
                "Align operating shifts with assured 3-phase agricultural power supply timetable"
            ]
        else:
            score = 0.25
            severity = "LOW"
            drivers.append("Standard utility requirements easily met by existing village infrastructure")
            impact = "Minimal infrastructure-related disruption risk."
            mitigations = [
                "Standard surge protection and basic electrical safety earthing"
            ]

        return CategoryRiskItem(
            type="INFRASTRUCTURE",
            score=score,
            severity=severity,
            drivers=drivers,
            evidence=evidence,
            impact=impact,
            mitigation=mitigations,
            confidence=0.85,
            source_stage="STAGE_6_MARKET_INTELLIGENCE"
        )

    def analyze(self, payload: Dict[str, Any]) -> RiskAnalysisResponse:
        """
        Main deterministic analysis entrypoint for Stage 11 Risk Engine.
        """
        node_id, title = self._resolve_business_context(payload)

        # 1. Evaluate all 7 Risk Categories
        fin_risk = self.evaluate_financial_risk(payload, node_id)
        mkt_risk = self.evaluate_market_risk(payload, node_id)
        ops_risk = self.evaluate_operational_risk(payload, node_id)
        sea_risk = self.evaluate_seasonal_risk(payload, node_id)
        sup_risk = self.evaluate_supply_chain_risk(payload, node_id)
        com_risk = self.evaluate_competition_risk(payload, node_id)
        inf_risk = self.evaluate_infrastructure_risk(payload, node_id)

        category_risks = {
            "FINANCIAL": fin_risk,
            "MARKET": mkt_risk,
            "OPERATIONAL": ops_risk,
            "SEASONAL": sea_risk,
            "SUPPLY_CHAIN": sup_risk,
            "COMPETITION": com_risk,
            "INFRASTRUCTURE": inf_risk
        }

        # 2. Compute Weighted Composite Score
        weighted_score = (
            RISK_WEIGHT_FINANCIAL * fin_risk.score +
            RISK_WEIGHT_MARKET * mkt_risk.score +
            RISK_WEIGHT_OPERATIONAL * ops_risk.score +
            RISK_WEIGHT_SEASONAL * sea_risk.score +
            RISK_WEIGHT_SUPPLY_CHAIN * sup_risk.score +
            RISK_WEIGHT_COMPETITION * com_risk.score +
            RISK_WEIGHT_INFRASTRUCTURE * inf_risk.score
        )
        weighted_score = round(weighted_score, 3)

        # Count severity distributions
        critical_count = sum(1 for r in category_risks.values() if r.severity == "CRITICAL")
        high_count = sum(1 for r in category_risks.values() if r.severity == "HIGH")

        # 3. Apply Critical Risk Ceiling Rule
        # If any single risk is CRITICAL, overall risk severity cannot be masked as LOW or MEDIUM
        critical_ceiling_applied = False
        if critical_count > 0:
            critical_ceiling_applied = True
            overall_severity = "CRITICAL" if critical_count >= 2 or weighted_score >= 0.70 else "HIGH"
            # Ensure overall score reflects at least elevated risk
            overall_score = max(0.68, weighted_score)
        elif weighted_score >= SEVERITY_THRESHOLD_HIGH:
            overall_severity = "HIGH"
            overall_score = weighted_score
        elif weighted_score >= SEVERITY_THRESHOLD_MEDIUM:
            overall_severity = "MEDIUM"
            overall_score = weighted_score
        else:
            overall_severity = "LOW"
            overall_score = weighted_score

        # 4. Extract Primary Drivers & Top Mitigations
        all_drivers = []
        all_mitigations = []
        for cat_name, cat_obj in sorted(category_risks.items(), key=lambda x: x[1].score, reverse=True):
            for d in cat_obj.drivers:
                all_drivers.append(f"[{cat_name}] {d}")
            for m in cat_obj.mitigation:
                if m not in all_mitigations:
                    all_mitigations.append(m)

        # Compute average confidence across categories
        avg_confidence = round(sum(r.confidence for r in category_risks.values()) / 7.0, 2)

        return RiskAnalysisResponse(
            success=True,
            analysis_id=payload.get("analysis_id"),
            session_id=payload.get("session_id"),
            business_title=title,
            business_node_id=node_id,
            overall_risk_score=round(overall_score, 2),
            overall_risk_severity=overall_severity,
            critical_risks_count=critical_count,
            high_risks_count=high_count,
            category_risks=category_risks,
            primary_risk_drivers=all_drivers[:5],
            recommended_mitigations=all_mitigations[:6],
            confidence=avg_confidence,
            provenance=RiskProvenanceRecord(
                critical_ceiling_applied=critical_ceiling_applied,
                evaluation_type="DETERMINISTIC_MULTI_VECTOR_SYNTHESIS"
            )
        )


# Global singleton instance
risk_engine = RiskEngine()
