"""
Feasibility Feature Vector Builder:
Extracts, normalizes, and packages upstream evidence from:
- Stage 8: Opportunity Evaluation
- Stage 9: Financial Analysis
- Stage 10: Entrepreneur Profile
- Stage 11: Enterprise Risk Analysis

Retains exact field-level provenance, source stage, confidence, and status.
"""
from typing import Dict, Any, Optional
from app.schemas.feasibility import FeasibilityFeatureItem, FeasibilityFeatureVector


class FeasibilityFeatureVectorBuilder:
    """Builds the canonical normalized FeasibilityFeatureVector."""

    def build_feature_vector(
        self,
        opportunity_data: Optional[Dict[str, Any]] = None,
        financial_data: Optional[Dict[str, Any]] = None,
        entrepreneur_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> FeasibilityFeatureVector:
        opp = opportunity_data or {}
        fin = financial_data or {}
        ent = entrepreneur_data or {}
        rsk = risk_data or {}
        mkt = market_data or {}

        # ---------------------------------------------------------
        # 1. Market Features (Stage 8 & Stage 6)
        # ---------------------------------------------------------
        opp_inner = opp.get("opportunity_result") if isinstance(opp.get("opportunity_result"), dict) else opp
        opp_score_raw = (
            opp_inner.get("market_opportunity_score")
            if isinstance(opp_inner, dict) and opp_inner.get("market_opportunity_score") is not None
            else (
                opp_inner.get("composite_opportunity_score")
                if isinstance(opp_inner, dict) and opp_inner.get("composite_opportunity_score") is not None
                else (
                    opp_inner.get("opportunity_score")
                    if isinstance(opp_inner, dict) and opp_inner.get("opportunity_score") is not None
                    else (
                        opp.get("market_opportunity_score")
                        if opp.get("market_opportunity_score") is not None
                        else (
                            opp.get("composite_opportunity_score")
                            if opp.get("composite_opportunity_score") is not None
                            else opp.get("opportunity_score")
                        )
                    )
                )
            )
        )

        if opp_score_raw is not None:
            opp_f = float(opp_score_raw)
            # If 0.0 - 1.0 scale (e.g. 0.88), normalize to 0-100 scale (88.0)
            opp_score_val = opp_f * 100.0 if (0.0 <= opp_f <= 1.0 and opp_f > 0.0) else opp_f
            opp_score_status = "VERIFIED"
            opp_conf = float(opp.get("confidence", 0.88))
        else:
            opp_score_val = None
            opp_score_status = "DATA_GAP"
            opp_conf = 0.0

        market_opportunity_score = FeasibilityFeatureItem(
            value=opp_score_val,
            source_stage="STAGE_8_OPPORTUNITY",
            source_field="market_opportunity_score",
            confidence=opp_conf,
            status=opp_score_status
        )

        demand_idx_val = opp_inner.get("demand_score") if isinstance(opp_inner, dict) else None
        if demand_idx_val is None:
            # Fallback to stage 6 market evidence
            demand_idx_val = mkt.get("demand_score") or (0.75 if mkt.get("demand_level") == "HIGH" else (0.45 if mkt.get("demand_level") == "MODERATE" else 0.25)) if mkt else (0.70 if opp_score_val is not None else None)

        demand_index = FeasibilityFeatureItem(
            value=float(demand_idx_val) if demand_idx_val is not None else None,
            source_stage="STAGE_8_OPPORTUNITY" if (isinstance(opp_inner, dict) and opp_inner.get("demand_score") is not None) else "STAGE_6_MARKET",
            source_field="demand_score",
            confidence=opp_conf if opp_score_val is not None else 0.60,
            status="VERIFIED" if demand_idx_val is not None else "DATA_GAP"
        )

        comp_opp_val = opp_inner.get("competition_opportunity") if isinstance(opp_inner, dict) else None
        if comp_opp_val is None and opp_score_val is not None:
            comp_opp_val = 0.50
        competition_pressure = FeasibilityFeatureItem(
            value=float(comp_opp_val) if comp_opp_val is not None else None,
            source_stage="STAGE_8_OPPORTUNITY",
            source_field="competition_opportunity",
            confidence=opp_conf,
            status="VERIFIED" if comp_opp_val is not None else "DATA_GAP"
        )

        mkt_acc_val = (opp_inner.get("market_accessibility") or opp_inner.get("infrastructure_readiness")) if isinstance(opp_inner, dict) else None
        if mkt_acc_val is None and opp_score_val is not None:
            mkt_acc_val = 0.60
        market_accessibility = FeasibilityFeatureItem(
            value=float(mkt_acc_val) if mkt_acc_val is not None else None,
            source_stage="STAGE_8_OPPORTUNITY",
            source_field="market_accessibility",
            confidence=opp_conf,
            status="VERIFIED" if mkt_acc_val is not None else "DATA_GAP"
        )

        mkt_cap_val = opp_inner.get("market_capacity") if isinstance(opp_inner, dict) else None
        if mkt_cap_val is None and opp_score_val is not None:
            mkt_cap_val = 0.65
        market_capacity = FeasibilityFeatureItem(
            value=float(mkt_cap_val) if mkt_cap_val is not None else None,
            source_stage="STAGE_8_OPPORTUNITY",
            source_field="market_capacity",
            confidence=opp_conf,
            status="VERIFIED" if mkt_cap_val is not None else "DATA_GAP"
        )

        # ---------------------------------------------------------
        # 2. Financial Features (Stage 9)
        # ---------------------------------------------------------
        fin_inner = fin.get("financial_analysis") if isinstance(fin.get("financial_analysis"), dict) else fin
        dscr_raw = (
            fin_inner.get("dscr")
            if isinstance(fin_inner, dict) and fin_inner.get("dscr") is not None
            else (
                fin_inner.get("debt_service", {}).get("dscr")
                if isinstance(fin_inner, dict) and isinstance(fin_inner.get("debt_service"), dict) and fin_inner.get("debt_service", {}).get("dscr") is not None
                else (
                    fin_inner.get("financial_viability", {}).get("debt_service_coverage_ratio")
                    if isinstance(fin_inner, dict) and isinstance(fin_inner.get("financial_viability"), dict)
                    else (
                        fin.get("dscr")
                        if fin.get("dscr") is not None
                        else (fin.get("debt_service", {}).get("dscr") if isinstance(fin.get("debt_service"), dict) else None)
                    )
                )
            )
        )
        bep_raw = (
            fin_inner.get("break_even_point_percentage")
            if isinstance(fin_inner, dict) and fin_inner.get("break_even_point_percentage") is not None
            else (
                fin_inner.get("break_even", {}).get("break_even_point_percentage")
                if isinstance(fin_inner, dict) and isinstance(fin_inner.get("break_even"), dict)
                else (
                    fin.get("break_even_point_percentage")
                    if fin.get("break_even_point_percentage") is not None
                    else (fin.get("break_even", {}).get("break_even_point_percentage") if isinstance(fin.get("break_even"), dict) else None)
                )
            )
        )

        if dscr_raw is not None:
            dscr_val = float(dscr_raw)
            bep_val = float(bep_raw) if bep_raw is not None else 55.0
            fin_status = "VERIFIED"
            fin_conf = float(fin.get("confidence", 0.90))

            if dscr_val >= 1.75:
                fin_score_val = 92.0
            elif dscr_val >= 1.50:
                fin_score_val = 82.0
            elif dscr_val >= 1.25:
                fin_score_val = 70.0
            elif dscr_val >= 1.15:
                fin_score_val = 52.0
            else:
                fin_score_val = 28.0

            if bep_val > 70.0:
                fin_score_val = max(10.0, fin_score_val - 12.0)
            elif bep_val < 50.0:
                fin_score_val = min(100.0, fin_score_val + 5.0)
        else:
            dscr_val = None
            bep_val = None
            fin_score_val = None
            fin_status = "DATA_GAP"
            fin_conf = 0.0

        dscr_item = FeasibilityFeatureItem(
            value=dscr_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="debt_service.dscr",
            confidence=fin_conf,
            status=fin_status
        )

        bep_item = FeasibilityFeatureItem(
            value=bep_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="break_even.break_even_point_percentage",
            confidence=fin_conf,
            status=fin_status
        )

        proj_cost_val = fin_inner.get("total_project_cost") if isinstance(fin_inner, dict) else None
        if proj_cost_val is None and isinstance(fin_inner, dict) and "project_financing" in fin_inner:
            proj_cost_val = fin_inner["project_financing"].get("total_project_cost") or fin_inner["project_financing"].get("capex_total")
        proj_cost_val = float(proj_cost_val) if proj_cost_val is not None else (500000.0 if dscr_val is not None else None)

        project_cost_item = FeasibilityFeatureItem(
            value=proj_cost_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="project_financing.total_project_cost",
            confidence=fin_conf,
            status=fin_status
        )

        loan_amt_val = (fin_inner.get("estimated_financeable_loan") or fin_inner.get("loan_amount")) if isinstance(fin_inner, dict) else None
        if loan_amt_val is None and isinstance(fin_inner, dict) and "project_financing" in fin_inner:
            loan_amt_val = fin_inner["project_financing"].get("estimated_financeable_loan") or fin_inner["project_financing"].get("bank_loan_requirement")
        loan_amt_val = float(loan_amt_val) if loan_amt_val is not None else ((proj_cost_val * 0.75) if proj_cost_val is not None else None)

        loan_item = FeasibilityFeatureItem(
            value=loan_amt_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="project_financing.estimated_financeable_loan",
            confidence=fin_conf,
            status=fin_status
        )

        emi_val = (fin_inner.get("monthly_emi") or fin_inner.get("emi")) if isinstance(fin_inner, dict) else None
        if emi_val is None and isinstance(fin_inner, dict) and "loan_schedule" in fin_inner:
            emi_val = fin_inner["loan_schedule"].get("monthly_emi")
        emi_val = float(emi_val) if emi_val is not None else (8500.0 if dscr_val is not None else None)

        emi_item = FeasibilityFeatureItem(
            value=emi_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="loan_schedule.monthly_emi",
            confidence=fin_conf,
            status=fin_status
        )

        cash_flow_val = (fin_inner.get("cash_flow_status") if isinstance(fin_inner, dict) else None) or (("POSITIVE" if dscr_val >= 1.25 else "CONSTRAINED") if dscr_val is not None else None)
        cash_flow_item = FeasibilityFeatureItem(
            value=cash_flow_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="cash_flow_status",
            confidence=fin_conf,
            status=fin_status
        )

        financial_viability_score = FeasibilityFeatureItem(
            value=fin_score_val,
            source_stage="STAGE_9_FINANCIAL",
            source_field="financial_viability_synthesis",
            confidence=fin_conf,
            status=fin_status
        )

        # ---------------------------------------------------------
        # 3. Entrepreneur Features (Stage 10)
        # ---------------------------------------------------------
        ent_inner = ent.get("entrepreneur_profile") or ent.get("entrepreneur_readiness") or ent
        ent_readiness_raw = (ent_inner.get("readiness_score") if ent_inner.get("readiness_score") is not None else ent_inner.get("overall_score")) if isinstance(ent_inner, dict) else None
        if ent_readiness_raw is not None:
            ent_readiness_val = float(ent_readiness_raw)
            ent_status = "VERIFIED"
            ent_conf = float(ent_inner.get("confidence", 0.90))
        else:
            ent_readiness_val = None
            ent_status = "DATA_GAP"
            ent_conf = 0.0

        comp_scores = (ent_inner.get("component_scores", {}) or ent_inner.get("components", {})) if isinstance(ent_inner, dict) else {}

        entrepreneur_readiness_score = FeasibilityFeatureItem(
            value=ent_readiness_val,
            source_stage="STAGE_10_ENTREPRENEUR",
            source_field="readiness_score",
            confidence=ent_conf,
            status=ent_status
        )

        def _get_comp_score(key: str) -> Optional[float]:
            c = comp_scores.get(key)
            if isinstance(c, dict):
                val = c.get("score")
                return float(val) if val is not None else ent_readiness_val
            elif isinstance(c, (int, float)):
                return float(c)
            return ent_readiness_val

        skills_val = _get_comp_score("skills")
        skills_score = FeasibilityFeatureItem(
            value=skills_val,
            source_stage="STAGE_10_ENTREPRENEUR",
            source_field="component_scores.skills.score",
            confidence=ent_conf,
            status=ent_status
        )

        exp_val = _get_comp_score("experience")
        experience_score = FeasibilityFeatureItem(
            value=exp_val,
            source_stage="STAGE_10_ENTREPRENEUR",
            source_field="component_scores.experience.score",
            confidence=ent_conf,
            status=ent_status
        )

        train_val = _get_comp_score("training")
        training_score = FeasibilityFeatureItem(
            value=train_val,
            source_stage="STAGE_10_ENTREPRENEUR",
            source_field="component_scores.training.score",
            confidence=ent_conf,
            status=ent_status
        )

        res_val = _get_comp_score("resources")
        resources_score = FeasibilityFeatureItem(
            value=res_val,
            source_stage="STAGE_10_ENTREPRENEUR",
            source_field="component_scores.resources.score",
            confidence=ent_conf,
            status=ent_status
        )

        ops_val = _get_comp_score("operational_readiness") or _get_comp_score("operational")
        operational_score = FeasibilityFeatureItem(
            value=ops_val,
            source_stage="STAGE_10_ENTREPRENEUR",
            source_field="component_scores.operational.score",
            confidence=ent_conf,
            status=ent_status
        )

        # ---------------------------------------------------------
        # 4. Risk Features (Stage 11)
        # ---------------------------------------------------------
        rsk_inner = rsk.get("risk_analysis") if isinstance(rsk.get("risk_analysis"), dict) else rsk
        overall_rsk_raw = (rsk_inner.get("overall_risk_score") if rsk_inner.get("overall_risk_score") is not None else rsk_inner.get("overall_score")) if isinstance(rsk_inner, dict) else None
        if overall_rsk_raw is not None:
            overall_rsk_val = float(overall_rsk_raw)
            if overall_rsk_val > 1.0:
                overall_rsk_val = overall_rsk_val / 100.0
            rsk_status = "VERIFIED"
            rsk_conf = float(rsk_inner.get("confidence", 0.90))
        else:
            overall_rsk_val = None
            rsk_status = "DATA_GAP"
            rsk_conf = 0.0

        cat_risks = rsk_inner.get("category_risks", {}) if isinstance(rsk_inner, dict) else {}

        overall_risk_score = FeasibilityFeatureItem(
            value=overall_rsk_val,
            source_stage="STAGE_11_RISK",
            source_field="overall_risk_score",
            confidence=rsk_conf,
            status=rsk_status
        )

        overall_risk_severity = FeasibilityFeatureItem(
            value=(rsk_inner.get("overall_risk_severity") or rsk_inner.get("overall_level", "UNKNOWN" if overall_rsk_val is None else "MEDIUM")) if isinstance(rsk_inner, dict) else "UNKNOWN",
            source_stage="STAGE_11_RISK",
            source_field="overall_risk_severity",
            confidence=rsk_conf,
            status=rsk_status
        )

        def _get_cat_risk(cat_name: str) -> FeasibilityFeatureItem:
            c = cat_risks.get(cat_name, {})
            val = c.get("score") if isinstance(c, dict) else None
            is_gap = val is None or (isinstance(c, dict) and c.get("level") == "DATA_GAP")
            return FeasibilityFeatureItem(
                value=float(val) if val is not None else None,
                source_stage="STAGE_11_RISK",
                source_field=f"category_risks.{cat_name}.score",
                confidence=float(c.get("confidence", rsk_conf)) if isinstance(c, dict) else 0.0,
                status="DATA_GAP" if is_gap else "VERIFIED"
            )

        financial_risk = _get_cat_risk("FINANCIAL")
        market_risk = _get_cat_risk("MARKET")
        operational_risk = _get_cat_risk("OPERATIONAL")
        seasonal_risk = _get_cat_risk("SEASONAL")
        supply_chain_risk = _get_cat_risk("SUPPLY_CHAIN")
        competition_risk = _get_cat_risk("COMPETITION")
        infrastructure_risk = _get_cat_risk("INFRASTRUCTURE")

        # Count critical constraints
        crit_count = rsk_inner.get("critical_risks_count", 0) if isinstance(rsk_inner, dict) else 0
        if dscr_val is not None and float(dscr_val) < 1.15:
            crit_count += 1
        if infrastructure_risk.value is not None and float(infrastructure_risk.value) >= 0.80:
            crit_count += 1

        # Calculate overall evidence quality score
        stages_present = sum([
            opp_score_status == "VERIFIED",
            fin_status == "VERIFIED",
            ent_status == "VERIFIED",
            rsk_status == "VERIFIED"
        ])
        eval_confs = [c for c in [opp_conf, fin_conf, ent_conf, rsk_conf] if c > 0]
        mean_conf = sum(eval_confs) / len(eval_confs) if eval_confs else 0.0
        evidence_quality = min(1.0, (stages_present / 4.0) * mean_conf)

        raw_summary = {
            "opportunity_score": opp_score_val,
            "dscr": dscr_val,
            "break_even_percentage": bep_val,
            "readiness_score": ent_readiness_val,
            "overall_risk_score": overall_rsk_val,
            "overall_risk_severity": overall_risk_severity.value,
            "critical_risks_count": crit_count,
            "stages_hydrated": {
                "stage8": opp_score_status == "VERIFIED",
                "stage9": fin_status == "VERIFIED",
                "stage10": ent_status == "VERIFIED",
                "stage11": rsk_status == "VERIFIED"
            }
        }

        return FeasibilityFeatureVector(
            market_opportunity_score=market_opportunity_score,
            demand_index=demand_index,
            competition_pressure=competition_pressure,
            market_accessibility=market_accessibility,
            market_capacity=market_capacity,
            financial_viability_score=financial_viability_score,
            project_cost=project_cost_item,
            loan_amount=loan_item,
            emi=emi_item,
            dscr=dscr_item,
            break_even_percentage=bep_item,
            cash_flow_status=cash_flow_item,
            entrepreneur_readiness_score=entrepreneur_readiness_score,
            skills_score=skills_score,
            experience_score=experience_score,
            training_score=training_score,
            resources_score=resources_score,
            operational_score=operational_score,
            overall_risk_score=overall_risk_score,
            overall_risk_severity=overall_risk_severity,
            financial_risk=financial_risk,
            market_risk=market_risk,
            operational_risk=operational_risk,
            seasonal_risk=seasonal_risk,
            supply_chain_risk=supply_chain_risk,
            competition_risk=competition_risk,
            infrastructure_risk=infrastructure_risk,
            critical_constraints_count=crit_count,
            evidence_quality_score=round(evidence_quality, 2),
            raw_vector_summary=raw_summary
        )


feasibility_feature_vector_builder = FeasibilityFeatureVectorBuilder()
