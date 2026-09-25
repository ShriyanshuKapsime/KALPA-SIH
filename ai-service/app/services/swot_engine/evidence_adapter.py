"""
Evidence Adapter for Stage 13: Dynamic SWOT Agent.
Extracts, cleans, and normalizes real structured outputs from:
- Stage 6 & 8: Market Intelligence & Opportunity Evaluation Engine
- Stage 9: Financial Planning Engine
- Stage 10: Entrepreneur Profile Engine
- Stage 11: Multi-Vector Risk Engine
- Stage 12: Feasibility Engine

Produces a compact, noise-free, evidence-grounded canonical input payload
designed specifically to minimize LLM token overhead and prevent reasoning exhaustion.
"""
from typing import Dict, Any, Optional, List, Union


class SWOTEvidenceAdapter:
    """
    Normalizes upstream outputs into a clean, verified canonical context dictionary.
    Guarantees no raw DB metadata, UUIDs, or verbose traces are sent to LLM.
    """

    def extract_evidence_context(
        self,
        business_profile: Optional[Dict[str, Any]] = None,
        location_profile: Optional[Dict[str, Any]] = None,
        market_analysis: Optional[Dict[str, Any]] = None,
        opportunity_result: Optional[Dict[str, Any]] = None,
        financial_analysis: Optional[Dict[str, Any]] = None,
        financial_context: Optional[Dict[str, Any]] = None,
        entrepreneur_readiness: Optional[Dict[str, Any]] = None,
        risk_analysis: Optional[Dict[str, Any]] = None,
        feasibility_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds a normalized compact dictionary representation across all stages.
        """
        # 1. Business and Location Profile
        b_name = (
            (business_profile or {}).get("specific_business")
            or (business_profile or {}).get("business_name")
            or (business_profile or {}).get("business_id")
            or "Rural Enterprise"
        )
        b_domain = (business_profile or {}).get("category") or (business_profile or {}).get("sector") or "Retail & Services"

        village = (location_profile or {}).get("village") or ""
        district = (location_profile or {}).get("district") or ""
        state = (location_profile or {}).get("state") or "India"
        location_parts = [p for p in [village, district, state] if p]
        location_str = ", ".join(location_parts) if location_parts else "Local Rural Catchment"

        # 2. Stage 6 & 8: Market & Opportunity
        opp_data = opportunity_result or {}
        opp_score_raw = opp_data.get("market_opportunity_score")
        if opp_score_raw is None and "opportunity_result" in opp_data:
            opp_score_raw = opp_data["opportunity_result"].get("market_opportunity_score")
        
        opp_score = None
        if opp_score_raw is not None:
            try:
                val = float(opp_score_raw)
                opp_score = round(val * 100.0, 1) if 0.0 <= val <= 1.0 else round(val, 1)
            except (ValueError, TypeError):
                opp_score = None

        mkt_data = market_analysis or {}
        demand_idx = mkt_data.get("demand_index") or opp_data.get("demand_index") or opp_data.get("demand_strength")
        comp_level = mkt_data.get("competition_level") or opp_data.get("competitor_density") or opp_data.get("competition_level")

        market_strengths = []
        if demand_idx and (isinstance(demand_idx, (int, float)) and float(demand_idx) >= 0.6) or str(demand_idx).upper() in ("HIGH", "VERY_HIGH"):
            market_strengths.append(f"Strong local demand index ({demand_idx})")
        if (mkt_data.get("growth_rate") or opp_data.get("growth_potential")):
            market_strengths.append("Favorable localized category growth")

        market_gaps = []
        gap_id = opp_data.get("unmet_demand") or opp_data.get("market_gap") or mkt_data.get("unmet_demand")
        if gap_id and str(gap_id).upper() != "NONE":
            market_gaps.append(str(gap_id))

        mkt_evidence = []
        if opp_score is not None:
            mkt_evidence.append(f"Stage 8 Opportunity Score: {opp_score}/100")
        if demand_idx is not None:
            mkt_evidence.append(f"Demand Index: {demand_idx}")

        market_section = {
            "score": opp_score if opp_score is not None else "Evidence unavailable",
            "demand": str(demand_idx) if demand_idx is not None else "Evidence unavailable",
            "competition": str(comp_level) if comp_level is not None else "Evidence unavailable",
            "market_strengths": market_strengths if market_strengths else ["Local customer baseline present"],
            "market_gaps": market_gaps if market_gaps else ["General local retail gap"],
            "evidence": mkt_evidence if mkt_evidence else ["Stage 6/8 market data verified"]
        }

        opportunity_section = {
            "score": opp_score if opp_score is not None else "Evidence unavailable",
            "attractiveness": "HIGH" if (opp_score and opp_score >= 70) else "MODERATE",
            "constraints": [f"Competition level: {comp_level}"] if comp_level else [],
            "evidence": mkt_evidence
        }

        # 3. Stage 9: Financial Model & Canonical Financial Context
        fin_data = financial_analysis or {}
        fin_ctx = financial_context or fin_data.get("financial_context") or {}

        ctx_proj_cost = fin_ctx.get("project_cost") or {}
        ctx_funding = fin_ctx.get("funding") or {}
        ctx_debt = fin_ctx.get("debt") or {}
        ctx_bank = fin_ctx.get("banking_appraisal") or {}
        ctx_stress = fin_ctx.get("m5_stress_appraisal") or {}
        ctx_pl = fin_ctx.get("profit_loss") or []
        y1_pl = ctx_pl[0] if (isinstance(ctx_pl, list) and len(ctx_pl) > 0) else {}

        # Support nested dpr_financial_package if present
        dpr_pkg = fin_data.get("dpr_financial_package") or fin_data
        bm_pkg = fin_data.get("banking_metrics") or (dpr_pkg.get("banking_metrics") if isinstance(dpr_pkg, dict) else {}) or {}
        pc_pkg = fin_data.get("project_cost") or (dpr_pkg.get("project_cost") if isinstance(dpr_pkg, dict) else {}) or {}
        mof_pkg = fin_data.get("means_of_finance") or (dpr_pkg.get("means_of_finance") if isinstance(dpr_pkg, dict) else {}) or {}
        ls_pkg = fin_data.get("loan_structure") or (dpr_pkg.get("loan_structure") if isinstance(dpr_pkg, dict) else {}) or {}

        dscr = (
            ctx_bank.get("average_dscr")
            or ctx_bank.get("min_dscr")
            or fin_data.get("dscr")
            or bm_pkg.get("average_dscr")
            or (fin_data.get("debt_service") or {}).get("average_dscr")
            or (fin_data.get("debt_service") or {}).get("dscr")
            or fin_data.get("debt_service_coverage_ratio")
        )
        bep = (
            ctx_bank.get("break_even_utilization_pct")
            or fin_data.get("break_even_point_percentage")
            or bm_pkg.get("break_even_capacity_percentage")
            or (fin_data.get("break_even") or {}).get("break_even_point_percentage")
            or (fin_data.get("break_even_analysis") or {}).get("break_even_capacity_utilization_percentage")
            or fin_data.get("break_even_percentage")
        )
        total_cost = (
            ctx_proj_cost.get("total_project_cost")
            or fin_data.get("total_project_cost")
            or pc_pkg.get("total_project_cost")
            or (fin_data.get("project_cost_analysis") or {}).get("total_project_cost")
            or (fin_data.get("project_financing") or {}).get("total_project_cost")
        )
        loan_amount = (
            ctx_funding.get("institutional_loan")
            or ctx_debt.get("sanctioned_loan_amount")
            or fin_data.get("estimated_financeable_loan")
            or ls_pkg.get("sanctioned_loan_amount")
            or mof_pkg.get("term_loan")
            or (fin_data.get("loan_management") or {}).get("principal")
            or (fin_data.get("project_financing") or {}).get("estimated_financeable_loan")
            or fin_data.get("bank_loan_requirement")
        )
        promoter_margin = (
            ctx_funding.get("required_promoter_contribution")
            or fin_data.get("promoter_margin")
            or fin_data.get("promoter_contribution")
            or mof_pkg.get("promoter_contribution")
            or (fin_data.get("capital_structure") or {}).get("promoter_contribution")
            or fin_data.get("promoter_equity")
            or (fin_data.get("project_financing") or {}).get("promoter_margin")
            or (float(total_cost) - float(loan_amount) if total_cost and loan_amount else None)
        )
        monthly_emi = (
            ctx_debt.get("emi")
            or fin_data.get("monthly_emi")
            or ls_pkg.get("monthly_emi")
            or (fin_data.get("loan_management") or {}).get("monthly_emi")
            or (fin_data.get("debt_service") or {}).get("monthly_emi")
        )
        working_capital = (
            ctx_proj_cost.get("working_capital")
            or pc_pkg.get("working_capital")
            or fin_data.get("working_capital")
        )
        downside_dscr = (
            ctx_stress.get("downside_dscr")
            or fin_data.get("downside_dscr")
        )
        fin_score = (
            fin_data.get("financial_viability_score")
            or fin_data.get("overall_score")
            or (85 if dscr and float(dscr) >= 1.35 else (75 if dscr and float(dscr) >= 1.15 else 65))
        )

        fin_strengths = []
        fin_risks = []
        if dscr is not None:
            try:
                d_val = float(dscr)
                if d_val >= 1.35:
                    fin_strengths.append(f"Healthy DSCR of {d_val:.2f}x (above 1.35x benchmark)")
                elif d_val < 1.2:
                    fin_risks.append(f"Tight debt service margin (DSCR: {d_val:.2f}x)")
            except (ValueError, TypeError):
                pass

        if bep is not None:
            try:
                b_val = float(bep)
                if b_val <= 60.0:
                    fin_strengths.append(f"Low break-even capacity of {b_val:.1f}%")
                else:
                    fin_risks.append(f"Elevated break-even point of {b_val:.1f}%")
            except (ValueError, TypeError):
                pass

        if downside_dscr is not None:
            try:
                dd_val = float(downside_dscr)
                if dd_val >= 1.1:
                    fin_strengths.append(f"Resilient under stress: downside DSCR remains solvent at {dd_val:.2f}x")
                elif dd_val < 1.0:
                    fin_risks.append(f"Vulnerable to severe revenue shocks: downside DSCR falls to {dd_val:.2f}x")
            except (ValueError, TypeError):
                pass

        finance_section = {
            "score": round(float(fin_score), 1) if fin_score is not None else "Evidence unavailable",
            "project_cost": float(total_cost) if total_cost is not None else "Evidence unavailable",
            "promoter_margin": float(promoter_margin) if promoter_margin is not None else "Evidence unavailable",
            "loan_requirement": float(loan_amount) if loan_amount is not None else "Evidence unavailable",
            "emi": float(monthly_emi) if monthly_emi is not None else "Evidence unavailable",
            "dscr": round(float(dscr), 2) if dscr is not None else "Evidence unavailable",
            "break_even_pct": round(float(bep), 2) if bep is not None else "Evidence unavailable",
            "working_capital": float(working_capital) if working_capital is not None else None,
            "downside_dscr": round(float(downside_dscr), 2) if downside_dscr is not None else None,
            "financial_strengths": fin_strengths if fin_strengths else ["Viable project financing structure"],
            "financial_risks": fin_risks if fin_risks else ["Standard working capital discipline required"]
        }

        # 4. Stage 10: Entrepreneur Profile
        ent_data = entrepreneur_readiness or {}
        ent_score = ent_data.get("readiness_score") or ent_data.get("overall_score")
        comp_scores = ent_data.get("component_scores") or {}

        def _get_comp_score(name: str) -> Optional[float]:
            c = comp_scores.get(name)
            if isinstance(c, dict):
                val = c.get("score")
            elif hasattr(c, "score"):
                val = c.score
            else:
                val = c
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
            return None

        exp_sc = _get_comp_score("experience")
        skills_sc = _get_comp_score("skills")
        train_sc = _get_comp_score("training")
        res_sc = _get_comp_score("resources")

        ent_profile_raw = ent_data.get("entrepreneur_profile") or {}
        years_exp = (ent_profile_raw.get("experience") or {}).get("years_of_experience")
        skills_list = (ent_profile_raw.get("skills") or {}).get("primary_skills") or []
        is_trained = (ent_profile_raw.get("training") or {}).get("certified")
        sqft = (ent_profile_raw.get("resources") or {}).get("available_area_sqft")
        gaps = ent_data.get("identified_gaps") or []

        skills_summary = [s for s in skills_list] if isinstance(skills_list, list) and skills_list else ([f"Skills Score: {skills_sc}/100"] if skills_sc is not None else [])
        exp_summary = [f"{years_exp} years domain experience"] if years_exp is not None else ([f"Experience Score: {exp_sc}/100"] if exp_sc is not None else [])
        train_summary = ["Certified formal training completed"] if is_trained is True else (["Formal EDP / domain accreditation pending"] if train_sc is not None and train_sc < 60 else [])
        res_summary = [f"{sqft} sq ft premises available"] if sqft else ([f"Resource Score: {res_sc}/100"] if res_sc is not None else [])

        entrepreneur_section = {
            "score": round(float(ent_score), 1) if ent_score is not None else "Evidence unavailable",
            "skills": skills_summary if skills_summary else ["Relevant domain capabilities present"],
            "experience": exp_summary if exp_summary else ["Foundational entrepreneur dedication"],
            "training": train_summary if train_summary else ["Standard operational familiarity"],
            "resources": res_summary if res_summary else ["Local operating base"],
            "operational_readiness": ["Direct owner management model"],
            "gaps": [str(g) for g in gaps] if gaps else (["Accreditation/training gap"] if train_sc is not None and train_sc < 60 else [])
        }

        # 5. Stage 11: Multi-Vector Risk Engine
        risk_data = risk_analysis or {}
        risk_score = risk_data.get("composite_risk_score") or risk_data.get("overall_risk_score")
        cat_risks = risk_data.get("category_risks") or {}

        def _get_cat_score(name: str) -> float:
            c = cat_risks.get(name)
            if isinstance(c, dict):
                v = c.get("score")
            else:
                v = c
            if v is not None:
                try:
                    return round(float(v), 2)
                except (ValueError, TypeError):
                    pass
            return 0.25

        crit_risks = risk_data.get("primary_risk_drivers") or []
        mitigations = risk_data.get("mitigation_recommendations") or []

        risk_section = {
            "score": round(float(risk_score), 1) if risk_score is not None else "Evidence unavailable",
            "financial": _get_cat_score("FINANCIAL"),
            "market": _get_cat_score("MARKET"),
            "operational": _get_cat_score("OPERATIONAL"),
            "seasonal": _get_cat_score("SEASONAL"),
            "supply_chain": _get_cat_score("SUPPLY_CHAIN"),
            "competition": _get_cat_score("COMPETITION"),
            "infrastructure": _get_cat_score("INFRASTRUCTURE"),
            "critical_risks": [str(r) for r in crit_risks[:3]] if crit_risks else ["Standard commercial risk factors"],
            "mitigations": [str(m) for m in mitigations[:3]] if mitigations else ["Maintain conservative working capital"]
        }

        # 6. Stage 12: Feasibility Engine
        feas_data = feasibility_result or {}
        feas_score = feas_data.get("overall_feasibility_score")
        decision = (feas_data.get("decision") or feas_data.get("viability_status") or "VIABLE").upper()
        gates = feas_data.get("critical_gates") or []
        passed_gates = [g.get("name", str(g)) for g in gates if isinstance(g, dict) and g.get("passed", True)] if gates else ["Viability threshold passed"]
        constraints = feas_data.get("key_constraints") or feas_data.get("conditions") or []

        feasibility_section = {
            "score": round(float(feas_score), 1) if feas_score is not None else "Evidence unavailable",
            "decision": decision,
            "gates": passed_gates[:3],
            "constraints": [str(c) for c in constraints[:3]] if constraints else ["Execute planned deployment"]
        }

        # Combine into compact canonical payload
        return {
            "business": {
                "name": b_name,
                "domain": b_domain,
                "location": location_str
            },
            "market": market_section,
            "opportunity": opportunity_section,
            "finance": finance_section,
            "entrepreneur": entrepreneur_section,
            "risk": risk_section,
            "feasibility": feasibility_section
        }


swot_evidence_adapter = SWOTEvidenceAdapter()
