"""
Milestone 6: DPR Validation & Completeness Evaluation.
Evaluates data completeness and institutional DPR readiness across M1–M5 outputs.
Enforces UNKNOWN != ZERO: does not silently manufacture missing values.
Integrates existing upstream validation checks (M3, M4, M5).
"""
from typing import Dict, Any, List, Optional
from app.services.financial_engine.dpr_packager.dpr_schema import (
    CompletenessStatus,
    FinancialEngineStatus,
    MetricDiagnostic,
    DataCompletenessPackage,
    ValidationFailureDetail,
)


class DPRValidationManager:
    """
    Evaluates institutional DPR data completeness and gate eligibility.
    Never invents arbitrary scores or default fallbacks.
    """

    # Essential fields required for an institutional-grade bankable DPR
    CORE_REQUIRED_FIELDS = [
        ("project_identity.project_name", "Project Name"),
        ("project_cost.total_project_cost", "Total Project Cost"),
        ("means_of_finance.promoter_contribution", "Promoter Margin Contribution"),
        ("means_of_finance.term_loan", "Term Loan Requirement"),
        ("working_capital.working_capital_requirement", "Working Capital Requirement"),
        ("revenue_operating_assumptions.annual_revenue_base", "Annual Base Revenue"),
        ("banking_metrics.first_year_pat", "Profit After Tax (Year 1)"),
        ("banking_metrics.dscr_y1", "Base DSCR (Year 1)"),
        ("loan_structure.monthly_emi", "Monthly Loan EMI"),
        ("loan_structure.annual_interest_rate_pct", "Interest Rate"),
        ("loan_structure.tenure_months", "Tenure"),
    ]

    SECONDARY_RECOMMENDED_FIELDS = [
        ("project_identity.nic_code", "NIC Code"),
        ("project_identity.district", "Location District"),
        ("banking_metrics.average_dscr", "Average DSCR"),
        ("banking_metrics.break_even_sales_amount", "Break-Even Sales"),
        ("m5_stress_appraisal.downside_dscr", "Downside Stressed DSCR"),
        ("m5_stress_appraisal.financing_resilience_status", "Financing Resilience Status"),
    ]

    def evaluate_completeness(
        self,
        package_dict: Dict[str, Any],
        m3_validation: Optional[Any] = None,
        m4_validation: Optional[Any] = None,
        m5_validation: Optional[Any] = None,
    ) -> DataCompletenessPackage:
        """
        Inspects canonical package dictionary and upstream validation objects to compute
        completeness statistics and determine whether the package is bankable.
        """
        all_checks = self.CORE_REQUIRED_FIELDS + self.SECONDARY_RECOMMENDED_FIELDS
        total_fields = len(all_checks)
        resolved_count = 0
        unresolved_fields: List[str] = []
        validation_failures: List[ValidationFailureDetail] = []

        # Check if project is explicitly debt-free / zero-debt
        rec_loan = self._extract_nested_value(package_dict, "m5_stress_appraisal.recommended_loan_amount")
        if rec_loan is None:
            rec_loan = self._extract_nested_value(package_dict, "loan_structure.term_loan")
        if rec_loan is None:
            rec_loan = self._extract_nested_value(package_dict, "loan_structure.total_debt")
        if rec_loan is None:
            rec_loan = self._extract_nested_value(package_dict, "means_of_finance.term_loan")
        is_zero_debt = (rec_loan is not None and float(rec_loan) == 0.0)

        for field_path, label in all_checks:
            val = self._extract_nested_value(package_dict, field_path)
            if is_zero_debt and "dscr" in field_path.lower():
                # Debt service coverage ratios are not applicable for debt-free (100% promoter equity) structures
                resolved_count += 1
            elif val is not None and val != "":
                resolved_count += 1
            else:
                unresolved_fields.append(f"{label} ({field_path})")

        # Extract upstream validation states
        m3_status = self._get_status(m3_validation)
        m4_status = self._get_status(m4_validation)
        m5_status = self._get_status(m5_validation)

        # Record failures from upstream M3
        if m3_validation:
            checks = getattr(m3_validation, "checks", []) or (m3_validation.get("checks", []) if isinstance(m3_validation, dict) else [])
            for c in checks:
                status = getattr(c, "status", None) or (c.get("status") if isinstance(c, dict) else None)
                if status in ("FAILED", "FAIL", "UNRESOLVED"):
                    cid = getattr(c, "check_id", "M3_CHECK") or (c.get("check_id", "M3_CHECK") if isinstance(c, dict) else "M3_CHECK")
                    msg = getattr(c, "message", "M3 statement check failed") or (c.get("message", "M3 statement check failed") if isinstance(c, dict) else "M3 statement check failed")
                    validation_failures.append(ValidationFailureDetail(
                        module="M3_STATEMENTS",
                        check_id=str(cid),
                        severity="ERROR" if status in ("FAILED", "FAIL") else "WARNING",
                        message=str(msg)
                    ))

        # Record failures from upstream M4
        if m4_validation:
            checks = getattr(m4_validation, "checks", []) or (m4_validation.get("checks", []) if isinstance(m4_validation, dict) else [])
            for c in checks:
                state = getattr(c, "state", None) or (c.get("state") if isinstance(c, dict) else None)
                if state in ("FAILED", "UNRESOLVED"):
                    cid = getattr(c, "check_id", "M4_CHECK") or (c.get("check_id", "M4_CHECK") if isinstance(c, dict) else "M4_CHECK")
                    desc = getattr(c, "description", "M4 appraisal check failed") or (c.get("description", "M4 appraisal check failed") if isinstance(c, dict) else "M4 appraisal check failed")
                    validation_failures.append(ValidationFailureDetail(
                        module="M4_APPRAISAL",
                        check_id=str(cid),
                        severity="ERROR" if state == "FAILED" else "WARNING",
                        message=str(desc)
                    ))

        # Record failures from upstream M5
        if m5_validation:
            checks = getattr(m5_validation, "checks", []) or (m5_validation.get("checks", []) if isinstance(m5_validation, dict) else [])
            for c in checks:
                state = getattr(c, "state", None) or (c.get("state") if isinstance(c, dict) else None)
                if state in ("FAILED", "UNRESOLVED"):
                    cid = getattr(c, "check_id", "M5_CHECK") or (c.get("check_id", "M5_CHECK") if isinstance(c, dict) else "M5_CHECK")
                    desc = getattr(c, "description", "M5 optimizer check failed") or (c.get("description", "M5 optimizer check failed") if isinstance(c, dict) else "M5 optimizer check failed")
                    validation_failures.append(ValidationFailureDetail(
                        module="M5_OPTIMIZER",
                        check_id=str(cid),
                        severity="ERROR" if state == "FAILED" else "WARNING",
                        message=str(desc)
                    ))

        # Determine overall completeness status
        core_unresolved = [
            f for f, lbl in self.CORE_REQUIRED_FIELDS
            if (not (is_zero_debt and "dscr" in f.lower()))
            and (self._extract_nested_value(package_dict, f) is None or self._extract_nested_value(package_dict, f) == "")
        ]

        if len(core_unresolved) == 0 and len(unresolved_fields) == 0:
            status = CompletenessStatus.COMPLETE
        elif len(core_unresolved) == 0 and len(unresolved_fields) > 0:
            status = CompletenessStatus.PARTIALLY_COMPLETE
        else:
            status = CompletenessStatus.INCOMPLETE

        # Evaluate Bankable DPR Gate:
        # Eligible if core required fields are resolved and upstream M3/M4/M5 are not hard FAILED
        dpr_gate_reasons: List[str] = []
        is_dpr_eligible = True

        if core_unresolved:
            is_dpr_eligible = False
            dpr_gate_reasons.append(f"Missing {len(core_unresolved)} critical core financial inputs.")

        if m3_status == "FAILED":
            is_dpr_eligible = False
            dpr_gate_reasons.append("Milestone 3 projection statements failed balance sheet or cash flow reconciliation.")

        if m4_status == "FAILED":
            is_dpr_eligible = False
            dpr_gate_reasons.append("Milestone 4 banking appraisal validation failed critical solvency or coverage thresholds.")

        if m5_status == "FAILED":
            is_dpr_eligible = False
            dpr_gate_reasons.append("Milestone 5 stress testing & financing optimizer failed debt sustainability or margin rules.")

        # Build structured metric diagnostics
        metric_diagnostics = self._build_metric_diagnostics(package_dict)

        has_blocking_metrics = any(d.is_blocking and d.status in ("NOT_AVAILABLE", "DISCLOSED_UNKNOWN") for d in metric_diagnostics)

        # Determine overall completeness status
        if core_unresolved or has_blocking_metrics:
            engine_status = FinancialEngineStatus.BLOCKED_PENDING_USER_INPUT
            is_dpr_eligible = False
            if has_blocking_metrics and not core_unresolved:
                dpr_gate_reasons.append("Mandatory financial DPR metrics require entrepreneur confirmation before bank packaging.")
        elif m3_status == "FAILED" or m4_status == "FAILED" or m5_status == "FAILED":
            engine_status = FinancialEngineStatus.ERROR
            is_dpr_eligible = False
        elif any(d.status in ("NOT_AVAILABLE", "DISCLOSED_UNKNOWN") and not d.is_blocking for d in metric_diagnostics):
            engine_status = FinancialEngineStatus.READY_WITH_DISCLOSED_UNKNOWNS
        else:
            engine_status = FinancialEngineStatus.READY_FOR_DPR

        # Generate blocking questions if blocked
        blocking_questions: List[Dict[str, Any]] = []
        if engine_status == FinancialEngineStatus.BLOCKED_PENDING_USER_INPUT:
            from app.services.financial_engine.intelligence.question_engine import question_engine
            field_to_driver = {
                "means_of_finance.promoter_contribution": "promoter_contribution",
                "revenue_operating_assumptions.annual_revenue_base": "selling_price",
                "project_cost.total_project_cost": "opening_inventory",
                "working_capital.working_capital_requirement": "opening_inventory",
                "profitability.annual_pat": "business_constitution",
                "banking_metrics.first_year_pat": "business_constitution",
                "pat": "business_constitution",
            }
            mock_assumptions = []
            for field_path in core_unresolved:
                driver_id = field_to_driver.get(field_path)
                if driver_id:
                    mock_assumptions.append({"driver_id": driver_id, "status": "USER_REQUIRED", "criticality": "HIGH"})
            for d in metric_diagnostics:
                if d.is_blocking and d.status in ("NOT_AVAILABLE", "DISCLOSED_UNKNOWN"):
                    driver_id = field_to_driver.get(d.metric_name) or d.metric_name
                    if driver_id not in [ma["driver_id"] for ma in mock_assumptions]:
                        mock_assumptions.append({"driver_id": driver_id, "status": "USER_REQUIRED", "criticality": "HIGH"})
            raw_qs = question_engine.generate_questions(mock_assumptions, language="en")
            top_q = question_engine.prioritize_blocking_question(raw_qs)
            if top_q:
                blocking_questions = [top_q.model_dump()]
            else:
                blocking_questions = [q.model_dump() for q in raw_qs]

        if is_dpr_eligible and engine_status == FinancialEngineStatus.READY_WITH_DISCLOSED_UNKNOWNS:
            dpr_gate_reasons.append("Eligible for bankable DPR package with disclosed non-blocking unknowns (e.g. tax treatment).")
        elif is_dpr_eligible and status == CompletenessStatus.PARTIALLY_COMPLETE:
            dpr_gate_reasons.append("Eligible for bankable DPR package with secondary benchmark indicators noted.")
        elif is_dpr_eligible:
            dpr_gate_reasons.append("All institutional credit appraisal criteria verified. Ready for bank submission.")

        return DataCompletenessPackage(
            status=status,
            financial_engine_status=engine_status,
            required_fields_total=total_fields,
            resolved_fields=resolved_count,
            unresolved_fields=unresolved_fields,
            metric_diagnostics=metric_diagnostics,
            blocking_questions=blocking_questions,
            m3_validation_status=m3_status,
            m4_validation_status=m4_status,
            m5_validation_status=m5_status,
            is_dpr_eligible=is_dpr_eligible,
            dpr_gate_reasons=dpr_gate_reasons,
            validation_failures=validation_failures
        )

    def _build_metric_diagnostics(self, pkg: Dict[str, Any]) -> List[MetricDiagnostic]:
        diagnostics: List[MetricDiagnostic] = []

        def _fmt_curr(val: Optional[float]) -> Optional[str]:
            return f"₹{val:,.0f}" if val is not None else None

        def _fmt_ratio(val: Optional[float]) -> Optional[str]:
            return f"{val:.2f}x" if val is not None else None

        # 1. Total Project Cost
        tpc = self._extract_nested_value(pkg, "project_cost.total_project_cost")
        diagnostics.append(MetricDiagnostic(
            metric_name="total_project_cost",
            display_name="Total Project Cost",
            status="CALCULATED" if tpc is not None else "NOT_AVAILABLE",
            value=tpc,
            formatted_value=_fmt_curr(tpc),
            source="PROJECT_COST_ENGINE",
            is_blocking=(tpc is None)
        ))

        # 2. CapEx
        capex = self._extract_nested_value(pkg, "project_cost.capex_subtotal")
        diagnostics.append(MetricDiagnostic(
            metric_name="capex",
            display_name="Fixed Capital (CapEx)",
            status="BENCHMARK" if capex is not None else "NOT_AVAILABLE",
            value=capex,
            formatted_value=_fmt_curr(capex),
            source="CAPEX_ENGINE",
            is_blocking=(capex is None)
        ))

        # 3. Working Capital
        wc = (
            self._extract_nested_value(pkg, "working_capital.working_capital_requirement")
            or self._extract_nested_value(pkg, "project_cost.working_capital_subtotal")
        )
        diagnostics.append(MetricDiagnostic(
            metric_name="working_capital",
            display_name="Working Capital Requirement",
            status="BENCHMARK" if wc is not None else "NOT_AVAILABLE",
            value=wc,
            formatted_value=_fmt_curr(wc),
            source="WORKING_CAPITAL_ENGINE",
            is_blocking=(wc is None)
        ))

        # 4. Annual Gross Revenue
        rev = self._extract_nested_value(pkg, "revenue_operating_assumptions.annual_revenue_base")
        diagnostics.append(MetricDiagnostic(
            metric_name="annual_revenue",
            display_name="Annual Gross Revenue (Year 1)",
            status="CALCULATED" if rev is not None else "NOT_AVAILABLE",
            value=rev,
            formatted_value=_fmt_curr(rev),
            source="PROFITABILITY_ENGINE",
            is_blocking=(rev is None)
        ))

        # 5. EBITDA
        ebitda = (
            self._extract_nested_value(pkg, "banking_metrics.first_year_ebitda")
            or self._extract_nested_value(pkg, "profitability.annual_ebitda")
        )
        diagnostics.append(MetricDiagnostic(
            metric_name="ebitda",
            display_name="Operating Profit (EBITDA)",
            status="CALCULATED" if ebitda is not None else "DISCLOSED_UNKNOWN",
            value=ebitda,
            formatted_value=_fmt_curr(ebitda),
            source="PROFITABILITY_ENGINE",
            reason_code=None if ebitda is not None else "DERIVATION_PENDING"
        ))

        # 6. PBT
        pbt = (
            self._extract_nested_value(pkg, "banking_metrics.first_year_pbt")
            or self._extract_nested_value(pkg, "profitability.annual_pbt")
        )
        diagnostics.append(MetricDiagnostic(
            metric_name="pbt",
            display_name="Profit Before Tax (PBT)",
            status="CALCULATED" if pbt is not None else "DISCLOSED_UNKNOWN",
            value=pbt,
            formatted_value=_fmt_curr(pbt),
            source="PROFITABILITY_ENGINE",
            reason_code=None if pbt is not None else "DERIVATION_PENDING"
        ))

        # 7. PAT (Net Profit After Tax)
        pat = (
            self._extract_nested_value(pkg, "banking_metrics.first_year_pat")
            or self._extract_nested_value(pkg, "profitability.annual_pat")
        )
        tax_status = (
            self._extract_nested_value(pkg, "banking_metrics.tax_status")
            or self._extract_nested_value(pkg, "profitability.tax_status")
            or "NOT_AVAILABLE"
        )
        if pat is not None:
            diagnostics.append(MetricDiagnostic(
                metric_name="pat",
                display_name="Net Profit After Tax (PAT)",
                status="CALCULATED",
                value=pat,
                formatted_value=_fmt_curr(pat),
                source="PROFITABILITY_ENGINE",
                is_blocking=False
            ))
        elif tax_status == "USER_CONFIRMED_UNRESOLVED":
            diagnostics.append(MetricDiagnostic(
                metric_name="pat",
                display_name="Net Profit After Tax (PAT)",
                status="DISCLOSED_UNKNOWN",
                value=None,
                formatted_value="Disclosed Unknown",
                source="TAX_POLICY_ENGINE",
                reason_code="TAX_TREATMENT_DISCLOSED_UNKNOWN",
                explanation="Entrepreneur opted to leave tax treatment unresolved. Disclosed as known unknown in bank credit package.",
                is_blocking=False
            ))
        else:
            diagnostics.append(MetricDiagnostic(
                metric_name="pat",
                display_name="Net Profit After Tax (PAT)",
                status="NOT_AVAILABLE",
                value=None,
                formatted_value="Pending Entity Registration" if tax_status == "PROVISIONAL_PENDING_REGISTRATION" else "Awaiting Tax Selection",
                source="TAX_POLICY_ENGINE",
                reason_code="TAX_TREATMENT_UNRESOLVED",
                explanation="PAT requires business constitution (Proprietorship, Partnership/LLP, or Company) to determine applicable statutory tax regime.",
                is_blocking=True
            ))

        # 8. Promoter Margin Contribution
        prom = self._extract_nested_value(pkg, "means_of_finance.promoter_contribution")
        diagnostics.append(MetricDiagnostic(
            metric_name="promoter_contribution",
            display_name="Promoter Margin Contribution",
            status="USER_PROVIDED" if prom is not None else "NOT_AVAILABLE",
            value=prom,
            formatted_value=_fmt_curr(prom),
            source="CAPITAL_STRUCTURE_ENGINE",
            is_blocking=(prom is None)
        ))

        # 9. Term Loan
        tloan = self._extract_nested_value(pkg, "means_of_finance.term_loan")
        diagnostics.append(MetricDiagnostic(
            metric_name="term_loan",
            display_name="Term Loan Requirement",
            status="CALCULATED" if tloan is not None else "NOT_AVAILABLE",
            value=tloan,
            formatted_value=_fmt_curr(tloan),
            source="DEBT_STRUCTURING_ENGINE",
            is_blocking=(tloan is None)
        ))

        # 10. Monthly Loan EMI
        emi = self._extract_nested_value(pkg, "loan_structure.monthly_emi")
        diagnostics.append(MetricDiagnostic(
            metric_name="monthly_emi",
            display_name="Monthly Loan EMI",
            status="CALCULATED" if emi is not None else "NOT_AVAILABLE",
            value=emi,
            formatted_value=_fmt_curr(emi),
            source="LOAN_SCHEDULE_ENGINE",
            is_blocking=(emi is None)
        ))

        # 11. DSCR (Year 1)
        rec_loan = self._extract_nested_value(pkg, "m5_stress_appraisal.recommended_loan_amount")
        if rec_loan is None:
            rec_loan = self._extract_nested_value(pkg, "loan_structure.term_loan")
        if rec_loan is None:
            rec_loan = self._extract_nested_value(pkg, "means_of_finance.term_loan")
        is_zd = (rec_loan is not None and float(rec_loan) == 0.0)

        dscr = self._extract_nested_value(pkg, "banking_metrics.dscr_y1")
        diagnostics.append(MetricDiagnostic(
            metric_name="dscr_y1",
            display_name="Base DSCR (Year 1)",
            status="CALCULATED" if dscr is not None else ("EXEMPT_ZERO_DEBT" if is_zd else "NOT_AVAILABLE"),
            value=dscr,
            formatted_value=_fmt_ratio(dscr) if dscr is not None else ("N/A (Debt-Free)" if is_zd else "Not available"),
            source="BANKING_APPRAISAL_ENGINE",
            is_blocking=(dscr is None and not is_zd)
        ))

        # 12. Break-Even Sales
        bes = self._extract_nested_value(pkg, "banking_metrics.break_even_sales_amount")
        diagnostics.append(MetricDiagnostic(
            metric_name="break_even_sales",
            display_name="Break-Even Sales Point",
            status="CALCULATED" if bes is not None else "DISCLOSED_UNKNOWN",
            value=bes,
            formatted_value=_fmt_curr(bes),
            source="BREAK_EVEN_ENGINE"
        ))

        return diagnostics

    def _extract_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        curr = data
        for k in keys:
            if isinstance(curr, dict):
                curr = curr.get(k)
            elif hasattr(curr, k):
                curr = getattr(curr, k)
            else:
                return None
            if curr is None:
                return None
        return curr

    @staticmethod
    def _get_status(val_obj: Any) -> Optional[str]:
        if not val_obj:
            return None
        if isinstance(val_obj, dict):
            return val_obj.get("status") or val_obj.get("state")
        return getattr(val_obj, "status", None) or getattr(val_obj, "state", None)


dpr_validation_manager = DPRValidationManager()
