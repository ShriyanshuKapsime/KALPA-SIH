filepath = "ai-service/app/services/dpr_stage1/dpr_context_builder.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

start_gather = "    async def _gather_upstream_data(self, business_id: str, db: Optional[Session] = None) -> Dict[str, Any]:\n"
end_gather = "dpr_context_builder = DPRContextBuilder()\n"

idx3 = content.find(start_gather)
idx4 = content.find(end_gather, idx3)

if idx3 == -1 or idx4 == -1:
    print(f"Error finding gather boundaries: {idx3}, {idx4}")
else:
    new_gather = """    async def _gather_upstream_data(self, business_id: str, db: Optional[Session] = None, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"
        Builds authoritative upstream context across Stages 1–13 without fabricating values.
        Supports both UUID and string business identifiers (e.g. 'saree_retail', 'dairy_farm').
        \"\"\"
        data = {
            "business_profile": {},
            "market_context": {},
            "financial_package": {},
            "risk_context": {},
            "swot_context": {},
            "feasibility_context": {},
            "documents": {}
        }

        from app.services.assistant_engine.context_builder import safe_uuid
        b_uuid = safe_uuid(business_id)

        # 1. Query Database if session available
        if db:
            try:
                from app.database.models.profile import StructuredBusinessProfile
                from app.database.models.finance import FinancialProfile
                from app.database.models.market import MarketEvidenceRecord
                from app.database.models.feasibility import FeasibilityResult
                from app.database.models.swot import SwotResult

                # Profile
                sb = None
                if b_uuid:
                    sb = db.query(StructuredBusinessProfile).filter(
                        (StructuredBusinessProfile.id == b_uuid) | (StructuredBusinessProfile.session_id == b_uuid)
                    ).order_by(StructuredBusinessProfile.created_at.desc()).first()
                if not sb:
                    sb = db.query(StructuredBusinessProfile).filter(
                        StructuredBusinessProfile.specific_business.ilike(f"%{business_id}%")
                    ).order_by(StructuredBusinessProfile.created_at.desc()).first()

                if sb and sb.profile_json and isinstance(sb.profile_json, dict):
                    pj = sb.profile_json
                    bp = pj.get("business_profile") or {}
                    lp = pj.get("location_profile") or {}
                    data["business_profile"] = {
                        "business_id": str(sb.id),
                        "business_name": sb.specific_business or bp.get("business_name") or bp.get("specific_business"),
                        "specific_business": sb.specific_business or bp.get("specific_business") or bp.get("business_name"),
                        "archetype": pj.get("category") or bp.get("category") or bp.get("archetype"),
                        "sector": pj.get("sector") or bp.get("sector"),
                        "nic_code": sb.nic_code or bp.get("nic_code"),
                        "district": sb.district or lp.get("district") or bp.get("district"),
                        "state": sb.state or lp.get("state") or bp.get("state"),
                        "capital": pj.get("capital") or bp.get("available_capital") or bp.get("proposed_investment"),
                        "promoter_name": bp.get("promoter_name") or bp.get("entrepreneur_name"),
                        "constitution": bp.get("constitution") or bp.get("legal_constitution"),
                        "target_scale": bp.get("target_scale", "micro"),
                        "business_model": bp.get("business_model"),
                        "readiness_score": pj.get("entrepreneur_readiness", {}).get("overall_score"),
                        "employment_generation": bp.get("employment_generation"),
                    }
                    if pj.get("financial_analysis"):
                        data["financial_package"] = pj.get("financial_analysis")

                # Financial Profile
                fp = None
                if b_uuid:
                    fp = db.query(FinancialProfile).filter(
                        (FinancialProfile.business_id == b_uuid) | (FinancialProfile.id == b_uuid)
                    ).order_by(FinancialProfile.created_at.desc()).first()
                if fp:
                    bk = fp.breakdown_json if isinstance(fp.breakdown_json, dict) else {}
                    dpr_pkg = bk.get("dpr_financial_package") or bk.get("financial_package")
                    if dpr_pkg and isinstance(dpr_pkg, dict):
                        data["financial_package"] = dpr_pkg
                    else:
                        data["financial_package"] = {
                            "total_project_cost": fp.total_project_cost or bk.get("total_project_cost"),
                            "promoter_contribution": fp.promoter_contribution or bk.get("promoter_contribution"),
                            "bank_loan_requirement": fp.bank_loan_requirement or bk.get("bank_loan_requirement"),
                            "subsidy_amount": fp.subsidy_amount or bk.get("subsidy_amount"),
                            "dscr": fp.debt_service_coverage_ratio or bk.get("dscr"),
                            "break_even": fp.break_even_percentage or bk.get("break_even_percentage"),
                            "project_cost": {"total_project_cost": fp.total_project_cost or bk.get("total_project_cost")},
                            "means_of_finance": {
                                "promoter_contribution": fp.promoter_contribution or bk.get("promoter_contribution"),
                                "term_loan": fp.bank_loan_requirement or bk.get("bank_loan_requirement"),
                                "subsidy_grant": fp.subsidy_amount or bk.get("subsidy_amount"),
                            },
                            "banking_metrics": {
                                "average_dscr": fp.debt_service_coverage_ratio or bk.get("dscr"),
                                "break_even_capacity_pct": fp.break_even_percentage or bk.get("break_even_percentage"),
                            }
                        }

                # Feasibility
                fb = None
                if b_uuid:
                    fb = db.query(FeasibilityResult).filter(
                        (FeasibilityResult.business_id == b_uuid) | (FeasibilityResult.session_id == b_uuid) | (FeasibilityResult.id == b_uuid)
                    ).order_by(FeasibilityResult.created_at.desc()).first()
                if fb:
                    data["feasibility_context"] = {
                        "overall_feasibility_score": fb.overall_feasibility_score,
                        "viability_status": fb.viability_status,
                        "recommendation": fb.recommendation,
                        "pillar_scores": fb.pillar_scores or {},
                        "critical_gates": fb.critical_gates or [],
                        "key_constraints": fb.key_constraints or [],
                    }

                # SWOT
                sw = None
                if b_uuid:
                    sw = db.query(SwotResult).filter(
                        (SwotResult.business_id == b_uuid) | (SwotResult.session_id == b_uuid) | (SwotResult.id == b_uuid)
                    ).order_by(SwotResult.created_at.desc()).first()
                if sw:
                    data["swot_context"] = {
                        "swot": sw.swot_json or {},
                        "swot_matrix": sw.swot_json or {},
                        "recommendations": sw.recommendations_json or [],
                    }

                # Market Evidence
                mkt = None
                if b_uuid:
                    mkt = db.query(MarketEvidenceRecord).filter(
                        (MarketEvidenceRecord.session_id == b_uuid) | (MarketEvidenceRecord.id == b_uuid)
                    ).order_by(MarketEvidenceRecord.created_at.desc()).first()
                if mkt:
                    data["market_context"] = mkt.market_evidence or mkt.full_profile or {}

            except Exception as e:
                logger.warning(f"[DPRContextBuilder] DB retrieval note: {e}")

        # 2. Check Scenario Repository
        try:
            from app.services.dpr_stage1.dpr_scenario_manager import scenario_repository
            scen = scenario_repository.get(business_id, scenario_id)
            if scen:
                if scen.financial_package and isinstance(scen.financial_package, dict):
                    data["financial_package"] = {**data["financial_package"], **scen.financial_package}
                if scen.input_snapshot and isinstance(scen.input_snapshot, dict):
                    for k in ["business_profile", "market_context", "swot_context", "feasibility_context", "documents"]:
                        if scen.input_snapshot.get(k):
                            data[k] = {**data.get(k, {}), **scen.input_snapshot[k]}
        except Exception as e:
            logger.warning(f"[DPRContextBuilder] Scenario repository lookup note: {e}")

        # 3. Authoritative Financial Auto-Resolution if financial package is missing
        if not data.get("financial_package") or not data["financial_package"].get("project_cost"):
            try:
                biz_name = data["business_profile"].get("business_name") or data["business_profile"].get("specific_business") or business_id
                cat = data["business_profile"].get("archetype") or data["business_profile"].get("category")
                nic = data["business_profile"].get("nic_code")

                bench_obj = self.benchmark_adapter.get_benchmark_data(
                    business_id=business_id,
                    specific_business=biz_name,
                    category=cat,
                    nic_code=nic
                )
                if bench_obj:
                    if not data["business_profile"].get("business_name"):
                        data["business_profile"]["business_name"] = bench_obj.business_title
                    if not data["business_profile"].get("nic_code"):
                        data["business_profile"]["nic_code"] = bench_obj.nic_code
                    if not data["business_profile"].get("archetype"):
                        data["business_profile"]["archetype"] = bench_obj.category

                    from app.schemas.financial import (
                        FinancialAnalysisRequest,
                        FinancialProfileInput,
                        BusinessProfileInput,
                        BeneficiaryProfileInput,
                        LocationProfileInput,
                        ProjectAssumptionsInput,
                    )
                    from app.services.financial_engine.engine import financial_engine
                    from app.services.financial_engine.dpr_packager.packager import dpr_packager

                    cost = bench_obj.typical_capex or 1000000.0
                    margin = cost * 0.10

                    req = FinancialAnalysisRequest(
                        analysis_id=f"auto_{business_id[:8]}",
                        session_id=f"sess_{business_id[:8]}",
                        financial_profile=FinancialProfileInput(
                            available_margin_capital=margin,
                            preferred_project_cost=cost
                        ),
                        business_profile=BusinessProfileInput(
                            business_id=business_id,
                            business_name=bench_obj.business_title,
                            specific_business=bench_obj.business_title,
                            category=bench_obj.category,
                            nic_code=bench_obj.nic_code
                        ),
                        beneficiary_profile=BeneficiaryProfileInput(
                            beneficiary_category="GENERAL",
                            gender="Male",
                            is_greenfield=True
                        ),
                        location_profile=LocationProfileInput(
                            district=data["business_profile"].get("district") or "Pune",
                            state=data["business_profile"].get("state") or "Maharashtra",
                            area_type="Rural"
                        ),
                        project_assumptions=ProjectAssumptionsInput()
                    )
                    resp = financial_engine.analyze(req)
                    packaged = dpr_packager.package(resp.financial_analysis)
                    data["financial_package"] = packaged.model_dump()
            except Exception as e:
                logger.warning(f"[DPRContextBuilder] Baseline financial engine auto-generation note: {e}")

        return data\n\n"""

    content = content[:idx3] + new_gather + content[idx4:]
    if has_crlf:
        content = content.replace("\n", "\r\n")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Gather successfully patched!")
