"""
Master Financial Projection & Statement Engine for Milestone 3.
Coordinates deterministic multi-year revenue, costs, P&L, cash flow, balance sheet,
ratios, sources & uses, validation, scenarios, and provenance.
100% deterministic Python financial arithmetic. Zero LLM calls.
"""
from typing import Dict, Any, List, Optional, Union
import datetime

from app.schemas.financial_analysis import (
    FinancialProjection,
    ProjectCostAnalysis,
    WorkingCapitalAnalysis,
    CapitalStructure,
    ProjectFinancing,
    LoanManagement,
    RepaymentSchedule,
    ProfitabilityProjection,
    ProjectAssumptionsInput,
    FundingSourcesUses,
    RevenueProjection,
    CostProjection,
    ProfitLossStatement,
    CashFlowStatement,
    BalanceSheet,
    WorkingCapitalProjection,
    FinancialRatioSet,
    ProjectionValidation,
)
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData
from app.services.financial_engine.constants import CALCULATION_VERSION

from app.services.financial_engine.projection.sources_uses import sources_uses_engine
from app.services.financial_engine.projection.revenue_projection import revenue_projection_engine
from app.services.financial_engine.projection.cost_projection import cost_projection_engine
from app.services.financial_engine.projection.depreciation import depreciation_engine
from app.services.financial_engine.projection.working_capital_projection import working_capital_projection_engine
from app.services.financial_engine.projection.profit_loss import profit_loss_engine
from app.services.financial_engine.projection.cash_flow_statement import cash_flow_statement_engine
from app.services.financial_engine.projection.balance_sheet import balance_sheet_engine
from app.services.financial_engine.projection.financial_ratios import financial_ratios_engine
from app.services.financial_engine.projection.validation import validation_engine
from app.services.financial_engine.projection.sensitivity import sensitivity_engine
from app.services.financial_engine.projection.provenance import provenance_engine


class ProjectionEngine:
    """
    Orchestrates the end-to-end multi-year projection and financial statement pipeline.
    """

    def project(
        self,
        projection_years: int = 5,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        working_capital_analysis: Optional[WorkingCapitalAnalysis] = None,
        capital_structure: Optional[CapitalStructure] = None,
        project_financing: Optional[ProjectFinancing] = None,
        loan_management: Optional[LoanManagement] = None,
        repayment_schedule: Optional[RepaymentSchedule] = None,
        profitability: Optional[ProfitabilityProjection] = None,
        project_assumptions: Optional[ProjectAssumptionsInput] = None,
        benchmark_data: Optional[BenchmarkFinancialData] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        assumptions_map: Optional[Dict[str, Any]] = None,
        scenario_inputs: Optional[Dict[str, Any]] = None,
        tax_rate: Optional[float] = None,
        business_profile: Optional[Any] = None,
        market_data: Optional[Dict[str, Any]] = None,
        allow_flat_base_case: bool = False,
    ) -> FinancialProjection:
        """
        Executes institutional deterministic 5-year projections and financial statements.
        """
        horizon = max(3, min(10, projection_years))
        user_in = user_inputs or {}
        asm_map = assumptions_map or {}

        # 1. Sources and Uses of Funds
        sources_uses = sources_uses_engine.build(
            project_cost_analysis=project_cost_analysis,
            capital_structure=capital_structure,
            project_financing=project_financing,
            user_inputs=user_in,
        )

        # 2. Driver-Based Revenue Projections
        rev_proj = revenue_projection_engine.project(
            projection_years=horizon,
            project_assumptions=project_assumptions,
            profitability=profitability,
            benchmark_data=benchmark_data,
            assumptions_map=asm_map,
            user_inputs=user_in,
            business_profile=business_profile,
            market_data=market_data,
            allow_flat_base_case=allow_flat_base_case,
        )

        # 3. Cost & Operating Expense Projections
        cost_proj = cost_projection_engine.project(
            revenue_projection=rev_proj,
            profitability=profitability,
            benchmark_data=benchmark_data,
            assumptions_map=asm_map,
            user_inputs=user_in,
        )

        # 4. Depreciation Schedule
        depr_sched = depreciation_engine.calculate_schedule(
            projection_years=horizon,
            project_cost_analysis=project_cost_analysis,
            capital_structure=capital_structure,
            user_inputs=user_in,
            benchmark_data=benchmark_data,
            assumptions_map=asm_map,
        )

        # 5. Multi-Year Working Capital Projections
        wc_proj = working_capital_projection_engine.project(
            revenue_projection=rev_proj,
            cost_projection=cost_proj,
            working_capital_analysis=working_capital_analysis,
            project_cost_analysis=project_cost_analysis,
            benchmark_data=benchmark_data,
            user_inputs=user_in,
            assumptions_map=asm_map,
        )

        # 6. Profit & Loss Statement (Year 1..N)
        pl_statement = profit_loss_engine.generate(
            revenue_projection=rev_proj,
            cost_projection=cost_proj,
            depreciation_schedule=depr_sched,
            repayment_schedule=repayment_schedule,
            sources_uses=sources_uses,
            user_inputs=user_in,
            tax_rate=tax_rate,
            business_profile=business_profile,
        )

        # 7. Cash Flow Statement (Year 0 + Year 1..N)
        cf_statement = cash_flow_statement_engine.generate(
            profit_loss=pl_statement,
            working_capital_proj=wc_proj,
            sources_uses=sources_uses,
            repayment_schedule=repayment_schedule,
        )

        # 8. Balance Sheet (Year 1..N)
        bs_statement = balance_sheet_engine.generate(
            profit_loss=pl_statement,
            cash_flow=cf_statement,
            working_capital_proj=wc_proj,
            sources_uses=sources_uses,
            depreciation_schedule=depr_sched,
            repayment_schedule=repayment_schedule,
            user_inputs=user_in,
            assumptions_map=asm_map,
        )

        # 9. Institutional Financial Ratios
        ratios = financial_ratios_engine.calculate(
            profit_loss=pl_statement,
            balance_sheet=bs_statement,
            working_capital_proj=wc_proj,
            cash_flow=cf_statement,
        )

        # 10. Accounting Invariants Validation
        val_result = validation_engine.validate(
            sources_uses=sources_uses,
            balance_sheet=bs_statement,
            cash_flow=cf_statement,
            profit_loss=pl_statement,
            working_capital_proj=wc_proj,
            financial_ratios=ratios,
            repayment_schedule=repayment_schedule,
        )

        # 11. Scenarios (Base, Upside, Downside)
        base_rev = rev_proj.base_annual_revenue
        base_cogs = cost_proj.years[0].cogs if cost_proj.years else None
        base_opex = cost_proj.years[0].total_operating_expenses if cost_proj.years else None

        scenarios = sensitivity_engine.evaluate_scenarios(
            base_annual_revenue=base_rev,
            base_annual_cogs=base_cogs,
            base_annual_opex=base_opex,
            scenario_inputs=scenario_inputs,
        )

        # 12. Provenance and Audit Trail
        prov_records = provenance_engine.build_records(
            revenue_projection=rev_proj,
            cost_projection=cost_proj,
            profit_loss=pl_statement,
            balance_sheet=bs_statement,
            working_capital_proj=wc_proj,
        )

        # Determine overall projection status
        # IF validation has FAILED checks: overall_status = "VALIDATION_FAILED"
        # ELIF validation has UNRESOLVED checks: overall_status = "PARTIALLY_DERIVED"
        # ELIF all required checks PASSED: continue normal RESOLVED logic
        if val_result.failed_checks > 0:
            overall_status = "VALIDATION_FAILED"
        elif val_result.unresolved_checks > 0:
            overall_status = "PARTIALLY_DERIVED"
        elif rev_proj.status == "INSUFFICIENT_DATA":
            overall_status = "INSUFFICIENT_DATA"
        elif pl_statement.status == "PARTIALLY_DERIVED" or bs_statement.status != "BALANCED":
            overall_status = "PARTIALLY_DERIVED"
        else:
            overall_status = "RESOLVED"

        conf = round((rev_proj.confidence + cost_proj.confidence + (1.0 if val_result.all_passed else 0.5)) / 3.0, 2)

        metadata = {
            "model_version": "financial-projection-v1",
            "calculation_version": CALCULATION_VERSION,
            "projection_horizon": horizon,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "llm_used": False,
        }

        return FinancialProjection(
            status=overall_status,
            projection_years=horizon,
            revenue_projection=rev_proj,
            cost_projection=cost_proj,
            profit_loss_statement=pl_statement,
            cash_flow_statement=cf_statement,
            balance_sheet=bs_statement,
            working_capital_projection=wc_proj,
            financial_ratios=ratios,
            funding_sources_uses=sources_uses,
            validation=val_result,
            scenarios=scenarios,
            provenance=prov_records,
            confidence=conf,
            metadata=metadata
        )


projection_engine = ProjectionEngine()
