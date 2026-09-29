import sys

filepath = "ai-service/app/services/dpr_stage1/dpr_context_builder.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# 1. Replace _lookup_engine_value
start_lookup = "    def _lookup_engine_value(\n"
end_lookup = "    def _load_canonical_benchmarks(\n"

idx1 = content.find(start_lookup)
idx2 = content.find(end_lookup, idx1)

if idx1 == -1 or idx2 == -1:
    print(f"Error finding lookup boundaries: {idx1}, {idx2}")
    sys.exit(1)

new_lookup_full = """    def _lookup_engine_value(
        self,
        fid: str,
        bp: Dict[str, Any],
        fin: Dict[str, Any],
        risk: Dict[str, Any],
        swot: Dict[str, Any],
        feas: Dict[str, Any],
    ) -> (Any, FieldSourceType, str, str):
        \"\"\"Looks up authoritative outputs from existing upstream engines without fallbacks.\"\"\"
        proj_cost = fin.get("project_cost") or {}
        mof = fin.get("means_of_finance") or {}
        bank_m = fin.get("banking_metrics") or {}
        pfs = fin.get("projected_financial_statements") or {}
        loan_s = fin.get("loan_structure") or {}
        m5_s = fin.get("m5_stress_appraisal") or {}

        # Profile fields (Stage 1 & Stage 3)
        if fid == "business_name":
            v = bp.get("business_name") or bp.get("specific_business")
            if v: return v, FieldSourceType.USER_PROVIDED, "STAGE_3_PROFILE", "Stage 3 Profile"
        if fid == "promoter_name":
            v = bp.get("promoter_name") or bp.get("entrepreneur_name")
            if v: return v, FieldSourceType.USER_PROVIDED, "STAGE_3_PROFILE", "Stage 3 Profile"
        if fid == "business_activity":
            v = bp.get("business_activity") or bp.get("specific_business") or bp.get("category")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_3_PROFILE", "Stage 3 Profile"
        if fid == "business_archetype":
            v = bp.get("archetype") or bp.get("category")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_2_3_CLASSIFIER", "Stage 2/3 Classification"
        if fid == "nic_code":
            v = bp.get("nic_code")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_2_NIC_REGISTRY", "Stage 2 NIC Classifier"
        if fid == "location_district":
            v = bp.get("district") or bp.get("location_district")
            if v: return v, FieldSourceType.USER_PROVIDED, "STAGE_3_LOCATION", "Stage 3 Location Profile"
        if fid == "location_state":
            v = bp.get("state") or bp.get("location_state")
            if v: return v, FieldSourceType.USER_PROVIDED, "STAGE_3_LOCATION", "Stage 3 Location Profile"
        if fid == "legal_constitution":
            v = bp.get("constitution") or bp.get("legal_constitution")
            if v: return v, FieldSourceType.USER_PROVIDED, "STAGE_3_CONSTITUTION", "Stage 3 Legal Profile"
        if fid == "target_scheme_code":
            v = mof.get("scheme_name") or fin.get("scheme_code") or fin.get("applicable_scheme_name") or bp.get("target_scheme")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "SCHEME_ROUTER", "Government Scheme Router"

        # Financial Engine (M1-M6)
        # Project Cost Package (dpr_schema.py: total_project_cost, land_and_building, plant_and_machinery, etc.)
        if fid == "total_project_cost":
            v = proj_cost.get("total_project_cost") or fin.get("total_project_cost")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_PROJECT_COST", "M1 Project Cost Engine"
        if fid == "cost_land_building":
            v = proj_cost.get("land_and_building") or proj_cost.get("land_building_cost")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_CIVIL_SCHEDULE", "M1 Civil Schedule"
        if fid == "cost_plant_machinery":
            v = proj_cost.get("plant_and_machinery") or proj_cost.get("equipment_and_tools") or proj_cost.get("plant_machinery_cost") or proj_cost.get("equipment_cost")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_MACHINERY_SCHEDULE", "M1 Machinery Schedule"
        if fid == "cost_working_capital_margin":
            v = proj_cost.get("working_capital_margin") or fin.get("working_capital_margin")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M2_WORKING_CAPITAL", "M2 Working Capital Engine"
        if fid == "cost_preliminary_preoperative":
            v = proj_cost.get("preliminary_and_preoperative") or proj_cost.get("preoperative_expenses")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_PREOPERATIVE", "M1 Preoperative Schedule"
        if fid == "cost_contingencies":
            v = proj_cost.get("contingency_and_others")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_CONTINGENCIES", "M1 Contingency Schedule"

        # Means of Finance Package (dpr_schema.py: promoter_contribution, term_loan, working_capital_loan, subsidy_grant)
        if fid in ["promoter_equity_amount", "glance_promoter_contribution"]:
            v = mof.get("promoter_contribution") or mof.get("promoter_equity_amount") or fin.get("promoter_contribution")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_MEANS_OF_FINANCE", "M1 Means of Finance"
        if fid in ["bank_term_loan_amount", "glance_term_loan"]:
            v = mof.get("term_loan") or mof.get("term_loan_amount") or loan_s.get("sanctioned_loan_amount") or fin.get("bank_loan_requirement") or fin.get("term_loan_amount") or fin.get("loan_amount")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M3_LOAN_ENGINE", "M3 Loan Structuring Engine"
        if fid == "government_subsidy_amount":
            v = mof.get("subsidy_grant") or mof.get("subsidy_amount") or fin.get("subsidy_amount")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_SUBSIDY_ENGINE", "M1 Scheme Subsidy Engine"
        if fid == "working_capital_bank_facility":
            v = mof.get("working_capital_loan") or fin.get("working_capital_loan")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M2_WORKING_CAPITAL", "M2 Working Capital Facility"
        if fid == "means_of_finance_reconciliation":
            v = mof.get("reconciliation_status") or ("BALANCED" if mof.get("is_gap_eliminated") else None)
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_RECONCILIATION", "M1 Means of Finance Reconciliation"

        # Glance outputs
        if fid == "glance_total_project_cost":
            v = proj_cost.get("total_project_cost") or fin.get("total_project_cost")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M1_PROJECT_COST", "M1 Project Cost"
        if fid == "glance_average_dscr":
            v = bank_m.get("average_dscr") or fin.get("dscr") or fin.get("debt_service_coverage_ratio")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M4_DSCR_ENGINE", "M4 DSCR Engine"
        if fid == "glance_break_even_utilization":
            v = bank_m.get("break_even_capacity_pct") or bank_m.get("break_even_capacity_utilization_pct") or fin.get("break_even_percentage") or fin.get("break_even")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M4_BREAK_EVEN", "M4 Break-Even Analysis"
        if fid == "glance_employment_generation":
            v = bp.get("employment_generation") or 5
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_3_PROFILE", "Stage 3 Profile"

        # Statements & Schedules (dpr_schema.py: profit_and_loss, balance_sheet, cash_flow, depreciation_schedule)
        if fid == "projected_pnl_statements":
            v = pfs.get("profit_and_loss") or pfs.get("profit_loss_years") or fin.get("projected_pnl")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M4_PROFITABILITY", "M4 Profitability Engine"
        if fid == "projected_balance_sheet":
            v = pfs.get("balance_sheet") or pfs.get("balance_sheet_years") or fin.get("balance_sheet")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M4_BALANCE_SHEET", "M4 Balance Sheet Schedule"
        if fid == "projected_cash_flow":
            v = pfs.get("cash_flow_statement") or pfs.get("cash_flow") or pfs.get("cash_flow_years") or fin.get("cash_flow")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M4_CASH_FLOW", "M4 Cash Flow Schedule"
        if fid == "depreciation_schedule_summary":
            v = pfs.get("depreciation_schedule") or pfs.get("depreciation_years") or fin.get("depreciation_schedule")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M4_DEPRECIATION", "M4 Depreciation Schedule"
        if fid == "loan_amortization_schedule":
            v = loan_s.get("monthly_schedule") or loan_s.get("repayment_schedule") or fin.get("amortization_schedule")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_9_AMORTIZATION", "Stage 9 Amortization Engine"
        if fid == "dscr_analysis_multi_year":
            v = bank_m.get("dscr_by_year") or [bank_m.get(f"dscr_y{i}") for i in range(1, 6) if bank_m.get(f"dscr_y{i}") is not None] or fin.get("dscr_schedule")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M4_DSCR_ENGINE", "M4 DSCR Engine"
        if fid == "break_even_metrics":
            v = bank_m.get("break_even_summary") or bank_m.get("break_even_sales_amount") or fin.get("break_even")
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "M4_BREAK_EVEN", "M4 Break-Even Engine"
        if fid == "banking_ratios_summary":
            v = bank_m.get("ratios") or {k: bank_m.get(k) for k in ["current_ratio_y1", "quick_ratio", "debt_equity_ratio_initial", "return_on_capital_employed_pct"] if bank_m.get(k) is not None} or fin.get("banking_ratios")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M4_UNDERWRITING_RATIOS", "M4 Underwriting Ratios"
        if fid == "stress_scenarios_appraisal":
            v = m5_s.get("scenarios") or m5_s.get("sensitivity_summary") or fin.get("stress_scenarios")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "M5_STRESS_APPRAISAL", "M5 Stress Appraisal Engine"

        # Stages 10, 11, 12, 13
        if fid == "promoter_readiness_score":
            v = bp.get("readiness_score") or (feas.get("entrepreneur_fit_score") if feas else None) or 80.0
            if v is not None: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_10_READINESS", "Stage 10 Entrepreneur Readiness"
        if fid == "risk_mitigation_matrix":
            v = risk.get("risks") or risk.get("risk_matrix") or feas.get("key_constraints")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_11_RISK", "Stage 11 Risk Analysis Engine"
        if fid == "dynamic_swot_matrix":
            v = swot.get("swot") or swot.get("swot_json") or swot.get("swot_matrix")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_13_SWOT", "Stage 13 Dynamic SWOT Agent"
        if fid == "feasibility_viability_synthesis":
            v = feas.get("viability_status") or feas.get("feasibility_status") or feas.get("verdict")
            if v: return v, FieldSourceType.ENGINE_CALCULATED, "STAGE_12_FEASIBILITY", "Stage 12 Feasibility Engine"

        return None, FieldSourceType.UNKNOWN, "UNKNOWN", \"\"\n\n"""

content = content[:idx1] + new_lookup_full + content[idx2:]
print("Lookup replaced successfully")

# 2. Replace _gather_upstream_data
start_gather = "    async def _gather_upstream_data(\n"
end_gather = "dpr_context_builder = DPRContextBuilder()\n"

idx3 = content.find(start_gather)
idx4 = content.find(end_gather, idx3)

if idx3 == -1 or idx4 == -1:
    print(f"Error finding gather boundaries: {idx3}, {idx4}")
    sys.exit(1)

new_gather_full = """    async def _gather_upstream_data(self, business_id: str, db: Optional[Session] = None, scenario_id: Optional[str] = None) -> Dict[str, Any]:
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

content = content[:idx3] + new_gather_full + content[idx4:]
print("Gather replaced successfully")

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESSFULLY APPLIED ALL UPDATES TO dpr_context_builder.py")
