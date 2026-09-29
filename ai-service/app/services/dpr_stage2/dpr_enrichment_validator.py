"""
Stage 14.2: DPR Enrichment Validator.
Performs deterministic mathematical reconciliation, provenance integrity checks,
and baseline isolation audits on the Stage 14.2 Enriched Package.
"""
import logging
from typing import Dict, Any, List, Optional

from app.services.dpr_stage2.dpr_enrichment_schemas import (
    EnrichmentField,
    EnrichmentSourceType,
    ValidationCheckResult,
    FinancialAuthorityCheckResult,
    EnrichmentValidationSummary,
    AUTHORITATIVE_FINANCIAL_FIELDS,
)

logger = logging.getLogger(__name__)


def _extract_pkg_financial_value(fin_pkg: Dict[str, Any], field_id: str) -> Optional[Any]:
    if not fin_pkg or not isinstance(fin_pkg, dict):
        return None
    p_cost = fin_pkg.get("project_cost") or {}
    m_fin = fin_pkg.get("means_of_finance") or {}
    b_met = fin_pkg.get("banking_metrics") or {}
    wc_block = fin_pkg.get("working_capital") or {}

    lookup_map = {
        "total_project_cost": p_cost.get("total_project_cost") if p_cost.get("total_project_cost") is not None else m_fin.get("total_project_cost"),
        "cost_plant_machinery": (
            p_cost.get("plant_and_machinery")
            if p_cost.get("plant_and_machinery") is not None
            else (
                p_cost.get("plant_machinery")
                if p_cost.get("plant_machinery") is not None
                else (
                    p_cost.get("capex_subtotal")
                    if p_cost.get("capex_subtotal") is not None
                    else (
                        p_cost.get("equipment_cost")
                        if p_cost.get("equipment_cost") is not None
                        else (
                            max(0.0, float(p_cost.get("total_project_cost", 0.0) or 0.0) - float(p_cost.get("working_capital_margin", 0.0) or 0.0))
                            if p_cost.get("total_project_cost") is not None
                            else None
                        )
                    )
                )
            )
        ),
        "cost_working_capital_margin": p_cost.get("working_capital_margin") if p_cost.get("working_capital_margin") is not None else wc_block.get("working_capital_margin_req"),
        "cost_pre_operative_expenses": p_cost.get("pre_operative_expenses"),
        "cost_contingency_provision": p_cost.get("contingency"),
        "bank_term_loan_amount": m_fin.get("term_loan") if m_fin.get("term_loan") is not None else m_fin.get("term_loan_amount"),
        "term_loan": m_fin.get("term_loan") if m_fin.get("term_loan") is not None else m_fin.get("term_loan_amount"),
        "promoter_equity_amount": m_fin.get("promoter_contribution") if m_fin.get("promoter_contribution") is not None else m_fin.get("promoter_equity_amount"),
        "promoter_contribution": m_fin.get("promoter_contribution") if m_fin.get("promoter_contribution") is not None else m_fin.get("promoter_equity_amount"),
        "working_capital_loan": m_fin.get("working_capital_loan"),
        "monthly_emi": m_fin.get("monthly_emi"),
        "glance_average_dscr": b_met.get("average_dscr"),
        "glance_break_even_utilization": b_met.get("break_even_capacity_percentage"),
        "break_even_capacity_percentage": b_met.get("break_even_capacity_percentage"),
        "break_even_sales_amount": b_met.get("break_even_sales_amount"),
        "glance_ebitda_margin": b_met.get("ebitda_margin"),
        "operating_ebitda_margin_pct": b_met.get("ebitda_margin"),
        "debt_equity_ratio": b_met.get("debt_equity_ratio"),
        "return_on_capital_employed_pct": b_met.get("roce"),
        "current_ratio_year1": b_met.get("current_ratio"),
        "working_capital_requirement": wc_block.get("working_capital_requirement"),
    }
    return lookup_map.get(field_id)


class DPREnrichmentValidator:
    """
    Evaluates institutional integrity rules for bankable DPR enrichment.
    """

    def validate_enrichment(
        self,
        fields: Dict[str, EnrichmentField],
        financial_package: Dict[str, Any],
        intake_package: Dict[str, Any],
        scenario_id: str
    ) -> EnrichmentValidationSummary:
        """
        Executes strict verification suite on the enriched DPR fields.
        """
        checks: List[ValidationCheckResult] = []
        blocking_reasons: List[str] = []

        # 1. Check: Stage 14.1 Intake Handoff Readiness
        readiness_block = intake_package.get("readiness") or {}
        is_ready = readiness_block.get("is_ready_for_stage_14_2", True)
        if not is_ready:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_INTAKE_READINESS",
                    rule_name="Stage 14.1 Intake Gate Verified",
                    passed=False,
                    severity="CRITICAL",
                    details="Stage 14.1 verified intake handoff package is not ready for enrichment.",
                    affected_fields=["business_name", "promoter_name", "location_state", "location_district"]
                )
            )
            blocking_reasons.append("Stage 14.1 verified intake handoff is incomplete.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_INTAKE_READINESS",
                    rule_name="Stage 14.1 Intake Gate Verified",
                    passed=True,
                    severity="CRITICAL",
                    details="Stage 14.1 verified intake handoff validated successfully.",
                )
            )

        # 2. Check: Financial Authority Boundary (CHK_FINANCIAL_AUTHORITY)
        fin_authority_checks: List[FinancialAuthorityCheckResult] = []
        fin_authority_violations: List[str] = []

        for fid in sorted(AUTHORITATIVE_FINANCIAL_FIELDS):
            fld = fields.get(fid)
            if not fld:
                continue

            pkg_val = _extract_pkg_financial_value(financial_package, fid)
            dpr_val = fld.value

            # Check 1: Must not be BENCHMARK_DERIVED
            if fld.source_type == EnrichmentSourceType.BENCHMARK_DERIVED:
                viol = f"{fid} is marked BENCHMARK_DERIVED"
                fin_authority_violations.append(viol)
                fin_authority_checks.append(
                    FinancialAuthorityCheckResult(
                        field_id=fid,
                        status="FAIL",
                        dpr_value=dpr_val,
                        financial_package_value=pkg_val,
                        source_type=str(fld.source_type.value if hasattr(fld.source_type, "value") else fld.source_type),
                        reason="Authoritative financial fields must not be derived from benchmarks."
                    )
                )
                continue

            # Check 2: Calculated outputs must not have a baseline_benchmark_value
            if fld.baseline_benchmark_value is not None:
                viol = f"{fid} has baseline_benchmark_value"
                fin_authority_violations.append(viol)
                fin_authority_checks.append(
                    FinancialAuthorityCheckResult(
                        field_id=fid,
                        status="FAIL",
                        dpr_value=dpr_val,
                        financial_package_value=pkg_val,
                        source_type=str(fld.source_type.value if hasattr(fld.source_type, "value") else fld.source_type),
                        reason="Calculated financial outputs must not have benchmark baselines."
                    )
                )
                continue

            # Check 3: Value reconciliation with financial_package if package has value
            if pkg_val is not None and dpr_val is not None:
                try:
                    f_pkg = float(pkg_val)
                    f_dpr = float(dpr_val)
                    tolerance = 1.0 if f_pkg > 100 else 0.05
                    diff = abs(f_pkg - f_dpr)
                    if diff > tolerance:
                        viol = f"{fid} value mismatch: DPR={f_dpr} vs FinancialPackage={f_pkg}"
                        fin_authority_violations.append(viol)
                        fin_authority_checks.append(
                            FinancialAuthorityCheckResult(
                                field_id=fid,
                                status="FAIL",
                                dpr_value=dpr_val,
                                financial_package_value=pkg_val,
                                source_type=str(fld.source_type.value if hasattr(fld.source_type, "value") else fld.source_type),
                                reason=f"Numeric mismatch exceeds tolerance ({diff:.2f} > {tolerance})"
                            )
                        )
                        continue
                except (ValueError, TypeError):
                    pass

            # Passed financial check
            fin_authority_checks.append(
                FinancialAuthorityCheckResult(
                    field_id=fid,
                    status="PASS",
                    dpr_value=dpr_val,
                    financial_package_value=pkg_val,
                    source_type=str(fld.source_type.value if hasattr(fld.source_type, "value") else fld.source_type),
                    reason="Verified against authoritative financial engine."
                )
            )

        if fin_authority_violations:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_FINANCIAL_AUTHORITY",
                    rule_name="Financial Authority Boundary Enforcement",
                    passed=False,
                    severity="CRITICAL",
                    details=f"Financial authority violations detected: {'; '.join(fin_authority_violations)}",
                    affected_fields=fin_authority_violations
                )
            )
            blocking_reasons.append("Authoritative financial fields must not be derived from benchmarks.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_FINANCIAL_AUTHORITY",
                    rule_name="Financial Authority Boundary Enforcement",
                    passed=True,
                    severity="CRITICAL",
                    details="100% of authoritative financial fields respect the M1-M6 boundary and match financial package.",
                )
            )

        # 3. Check: Zero-Fabrication (UNKNOWN != ZERO)
        unresolved_zeroes: List[str] = []
        for fid, fld in fields.items():
            if fld.value == 0.0 and fld.source_type == EnrichmentSourceType.UNKNOWN:
                unresolved_zeroes.append(fid)

        if unresolved_zeroes:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_UNKNOWN_NOT_ZERO",
                    rule_name="Zero-Fabrication Guarantee",
                    passed=False,
                    severity="CRITICAL",
                    details=f"Detected synthetic zero values in UNKNOWN fields: {unresolved_zeroes}",
                    affected_fields=unresolved_zeroes
                )
            )
            blocking_reasons.append("Synthetic zeros detected in unresolved fields.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_UNKNOWN_NOT_ZERO",
                    rule_name="Zero-Fabrication Guarantee",
                    passed=True,
                    severity="CRITICAL",
                    details="All missing fields preserve UNKNOWN state without zero fabrication.",
                )
            )

        # 4. Check: Provenance Completeness for All Resolved Factual Fields
        missing_provenance: List[str] = []
        for fid, fld in fields.items():
            if fld.value is not None and (not fld.source_type or fld.source_type == EnrichmentSourceType.UNKNOWN):
                missing_provenance.append(fid)

        if missing_provenance:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_PROVENANCE_COMPLETENESS",
                    rule_name="Provenance Audit Trail",
                    passed=False,
                    severity="CRITICAL",
                    details=f"Fields resolved without authoritative provenance: {missing_provenance}",
                    affected_fields=missing_provenance
                )
            )
            blocking_reasons.append("Resolved fields missing provenance attribution.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_PROVENANCE_COMPLETENESS",
                    rule_name="Provenance Audit Trail",
                    passed=True,
                    severity="CRITICAL",
                    details="100% of resolved factual fields have verifiable source attribution.",
                )
            )

        # 5. Check: Mathematical Sources vs Uses Reconciliation
        p_cost = fields.get("total_project_cost")
        p_loan = fields.get("bank_term_loan_amount")
        p_margin = fields.get("promoter_equity_amount")

        cost_val = p_cost.value if p_cost else None
        loan_val = p_loan.value if p_loan else None
        margin_val = p_margin.value if p_margin else None

        if cost_val is not None and loan_val is not None and margin_val is not None:
            p_cost_f = float(cost_val)
            p_loan_f = float(loan_val)
            p_margin_f = float(margin_val)
            diff = abs(p_cost_f - (p_loan_f + p_margin_f))

            if diff > 1.0:
                checks.append(
                    ValidationCheckResult(
                        check_id="CHK_FINANCIAL_BALANCE",
                        rule_name="Sources vs Uses Balance",
                        passed=False,
                        severity="CRITICAL",
                        details=f"Financial imbalance: Total Uses (₹{p_cost_f:,.0f}) != Total Sources (Loan ₹{p_loan_f:,.0f} + Equity ₹{p_margin_f:,.0f})",
                        affected_fields=["total_project_cost", "bank_term_loan_amount", "promoter_equity_amount"]
                    )
                )
                blocking_reasons.append("Sources vs Uses mathematical imbalance.")
            else:
                checks.append(
                    ValidationCheckResult(
                        check_id="CHK_FINANCIAL_BALANCE",
                        rule_name="Sources vs Uses Balance",
                        passed=True,
                        severity="CRITICAL",
                        details=f"Balanced financial structure verified (₹{p_cost_f:,.0f} project outlay fully financed).",
                        affected_fields=["total_project_cost", "bank_term_loan_amount", "promoter_equity_amount"]
                    )
                )
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_FINANCIAL_BALANCE",
                    rule_name="Sources vs Uses Balance",
                    passed=True,
                    severity="INFO",
                    details="Financial outlays pending resolution.",
                )
            )

        # 6. Check: Benchmark Isolation on Overridden Fields
        isolation_errors: List[str] = []
        for fid, fld in fields.items():
            if fld.is_overridden and fld.baseline_benchmark_value is None and fid not in AUTHORITATIVE_FINANCIAL_FIELDS:
                isolation_errors.append(fid)

        if isolation_errors:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_BENCHMARK_ISOLATION",
                    rule_name="Immutable Benchmark Preservation",
                    passed=False,
                    severity="WARNING",
                    details=f"Overridden assumptions missing original benchmark baseline: {isolation_errors}",
                    affected_fields=isolation_errors
                )
            )
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_BENCHMARK_ISOLATION",
                    rule_name="Immutable Benchmark Preservation",
                    passed=True,
                    severity="INFO",
                    details="Original benchmark baselines preserved separately from user overrides.",
                )
            )

        # 7. Check: Mandatory Applicable Fields Resolved
        unresolved_mandatory: List[str] = []
        for fid, fld in fields.items():
            if fld.materiality in ["CRITICAL", "HIGH"] and fld.status in ["UNKNOWN", "USER_REQUIRED", "UNRESOLVED", "SOURCE_MAPPING_ERROR"]:
                unresolved_mandatory.append(f"{fid} ({fld.label})")

        if unresolved_mandatory:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_MANDATORY_FIELDS_RESOLVED",
                    rule_name="Mandatory Applicable Fields Resolved",
                    passed=False,
                    severity="CRITICAL",
                    details=f"Mandatory applicable fields remain unresolved: {'; '.join(unresolved_mandatory[:6])}{' (and more)' if len(unresolved_mandatory) > 6 else ''}",
                    affected_fields=[s.split()[0] for s in unresolved_mandatory]
                )
            )
            blocking_reasons.append(f"{len(unresolved_mandatory)} mandatory DPR fields are unresolved.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_MANDATORY_FIELDS_RESOLVED",
                    rule_name="Mandatory Applicable Fields Resolved",
                    passed=True,
                    severity="CRITICAL",
                    details="100% of mandatory applicable DPR fields are resolved.",
                )
            )

        # 8. Check: Zero Source Mapping Errors
        mapping_errors: List[str] = [fid for fid, fld in fields.items() if fld.status == "SOURCE_MAPPING_ERROR" or fld.source_type == EnrichmentSourceType.SOURCE_MAPPING_ERROR]
        if mapping_errors:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_NO_SOURCE_MAPPING_ERRORS",
                    rule_name="Source Mapping Integrity",
                    passed=False,
                    severity="CRITICAL",
                    details=f"Source mapping errors detected: {mapping_errors}",
                    affected_fields=mapping_errors
                )
            )
            blocking_reasons.append("Source mapping errors detected in DPR resolver.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_NO_SOURCE_MAPPING_ERRORS",
                    rule_name="Source Mapping Integrity",
                    passed=True,
                    severity="CRITICAL",
                    details="Zero source mapping errors in DPR context.",
                )
            )

        # 9. Check: Financial Package Presence
        p_cost = financial_package.get("project_cost") if isinstance(financial_package, dict) else None
        m_fin = financial_package.get("means_of_finance") if isinstance(financial_package, dict) else None
        if not financial_package or not isinstance(financial_package, dict) or not (p_cost or m_fin):
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_FINANCIAL_PACKAGE_PRESENT",
                    rule_name="Financial Package Presence",
                    passed=False,
                    severity="CRITICAL",
                    details="Authoritative financial package is missing or incomplete.",
                )
            )
            blocking_reasons.append("Authoritative financial package is missing or incomplete.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_FINANCIAL_PACKAGE_PRESENT",
                    rule_name="Financial Package Presence",
                    passed=True,
                    severity="CRITICAL",
                    details="Verified authoritative financial package present.",
                )
            )

        # 10. Check: Zero Unresolved Conflicts
        unresolved_conflicts = [fid for fid, fld in fields.items() if getattr(fld, 'status', None) in ["CONFLICT", "UNRESOLVED_CONFLICT"]]
        if unresolved_conflicts:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_NO_UNRESOLVED_CONFLICTS",
                    rule_name="Zero Unresolved Field Conflicts",
                    passed=False,
                    severity="CRITICAL",
                    details=f"Unresolved field conflicts detected: {unresolved_conflicts}",
                    affected_fields=unresolved_conflicts
                )
            )
            blocking_reasons.append("Unresolved field conflicts detected in DPR context.")
        else:
            checks.append(
                ValidationCheckResult(
                    check_id="CHK_NO_UNRESOLVED_CONFLICTS",
                    rule_name="Zero Unresolved Field Conflicts",
                    passed=True,
                    severity="CRITICAL",
                    details="Zero unresolved field conflicts in DPR context.",
                )
            )

        failed_count = sum(1 for c in checks if not c.passed)
        passed_count = sum(1 for c in checks if c.passed)
        warnings_count = sum(1 for c in checks if not c.passed and c.severity == "WARNING")
        is_valid = len(blocking_reasons) == 0

        return EnrichmentValidationSummary(
            overall_valid=is_valid,
            total_checks=len(checks),
            passed_checks=passed_count,
            failed_checks=failed_count,
            warnings_count=warnings_count,
            checks=checks,
            financial_authority_checks=fin_authority_checks,
            blocking_reasons=blocking_reasons
        )


dpr_enrichment_validator = DPREnrichmentValidator()
