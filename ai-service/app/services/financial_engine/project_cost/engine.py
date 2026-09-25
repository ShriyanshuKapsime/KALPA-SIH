"""
Milestone 2: Master Deterministic Project Cost Engine.
Coordinates:
- Derivation of interdependent financial drivers (DerivationEngine)
- Archetype-specific Working Capital calculation (WorkingCapitalEngine)
- Deterministic CapEx decomposition (CapExEngine)
- Pre-operative / setup cost identification
- Benchmark-supported contingency identification (ONLY when justified)
- Promoter margin & Debt financing split
- Project cost reconciliation against scheme financeable capacity (ProjectCostReconciler)
- Strict provenance and confidence tracking for every component.

NEVER invents financial amounts. Returns explicit UNKNOWN / INSUFFICIENT_DATA when evidence is lacking.
Zero LLM calculations.
"""
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from app.schemas.financial_analysis import (
    ProjectCostAnalysis,
    ProjectCostComponent,
    CapExDecomposition,
    ProjectCostReconciliation,
    WorkingCapitalAnalysis,
)
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, SourceType, AssumptionStatus, Provenance
)
from app.services.financial_engine.intelligence.archetype_registry import FinancialArchetype, archetype_registry
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData, financial_benchmark_adapter
from app.services.financial_engine.project_cost.derivation import derivation_engine, DerivationEngine
from app.services.financial_engine.project_cost.working_capital import working_capital_engine, WorkingCapitalEngine
from app.services.financial_engine.project_cost.capex import capex_engine, CapExEngine
from app.services.financial_engine.project_cost.reconciliation import project_cost_reconciler, ProjectCostReconciler

logger = logging.getLogger(__name__)


class ProjectCostEngine:
    """
    Institutional-grade deterministic Project Cost and Working Capital intelligence engine.
    """

    def __init__(
        self,
        derivation_eng: Optional[DerivationEngine] = None,
        wc_eng: Optional[WorkingCapitalEngine] = None,
        cx_eng: Optional[CapExEngine] = None,
        reconciler: Optional[ProjectCostReconciler] = None,
    ):
        self.derivation_engine = derivation_eng or derivation_engine
        self.working_capital_engine = wc_eng or working_capital_engine
        self.capex_engine = cx_eng or capex_engine
        self.reconciler = reconciler or project_cost_reconciler

    def evaluate(
        self,
        archetype: FinancialArchetype,
        assumptions: List[ResolvedAssumption],
        benchmark_data: Optional[Union[BenchmarkFinancialData, Dict[str, Any]]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        scheme_financeable_cost: Optional[float] = None,
        scheme_margin_ratio: float = 0.10,
        preferred_project_cost: Optional[float] = None,
    ) -> Tuple[ProjectCostAnalysis, WorkingCapitalAnalysis, List[ResolvedAssumption]]:
        """
        Executes complete deterministic project cost decomposition and reconciliation.
        Returns:
            (ProjectCostAnalysis, WorkingCapitalAnalysis, List[ResolvedAssumption])
        """
        user_inputs = user_inputs or {}

        # ---------------------------------------------------------------------
        # 1. Run M2 Derivation Engine over M1 assumptions
        # ---------------------------------------------------------------------
        derived_assumptions = self.derivation_engine.resolve_derivations(
            archetype=archetype,
            assumptions=assumptions,
            user_inputs=user_inputs,
        )
        asm_map: Dict[str, ResolvedAssumption] = {a.driver_id: a for a in derived_assumptions}

        # ---------------------------------------------------------------------
        # 2. Run Working Capital Engine
        # ---------------------------------------------------------------------
        wc_analysis = self.working_capital_engine.calculate(
            archetype=archetype,
            assumptions=derived_assumptions,
            benchmark_data=benchmark_data,
            user_inputs=user_inputs,
        )

        # ---------------------------------------------------------------------
        # 3. Determine Opening Inventory
        # Priority: USER_INPUT -> BENCHMARK -> DERIVED (from WC inventory) -> UNKNOWN
        # ---------------------------------------------------------------------
        components: List[ProjectCostComponent] = []
        provenance_list: List[Dict[str, Any]] = []
        confidences: List[float] = []

        opening_inv: Optional[float] = None
        inv_comp: Optional[ProjectCostComponent] = None

        if "opening_inventory" in asm_map and asm_map["opening_inventory"].value is not None:
            user_inv_asm = asm_map["opening_inventory"]
            opening_inv = float(user_inv_asm.value)
            inv_comp = ProjectCostComponent(
                component_id="opening_inventory",
                name="Opening Stock & Raw Materials",
                amount=opening_inv,
                unit="INR",
                source_type=user_inv_asm.source_type.value,
                source_id=user_inv_asm.source_id,
                confidence=user_inv_asm.confidence,
                calculation_method=user_inv_asm.notes,
                provenance=user_inv_asm.provenance.model_dump() if user_inv_asm.provenance else None,
                status=user_inv_asm.status.value,
                explanation=f"Opening inventory investment from {user_inv_asm.source_type.value}."
            )
        elif wc_analysis.inventory_requirement is not None and wc_analysis.inventory_requirement > 0:
            opening_inv = float(wc_analysis.inventory_requirement)
            inv_comp = ProjectCostComponent(
                component_id="opening_inventory",
                name="Opening Stock & Raw Materials",
                amount=opening_inv,
                unit="INR",
                source_type="DERIVED",
                source_id="WORKING_CAPITAL_INVENTORY_REQUIREMENT",
                confidence=wc_analysis.confidence,
                calculation_method="derived_from_working_capital_operating_cycle",
                provenance={
                    "source_type": "DERIVED",
                    "source_id": "WC_INVENTORY_HOLDING",
                    "description": f"Opening inventory derived from operating cycle requirement: ₹{opening_inv:,.2f}",
                    "confidence": wc_analysis.confidence
                },
                status="CALCULATED",
                explanation=f"Opening inventory derived from {archetype.value} inventory holding requirement."
            )
        elif archetype in (FinancialArchetype.SERVICE, FinancialArchetype.REPAIR, FinancialArchetype.AGRICULTURE, FinancialArchetype.LIVESTOCK):
            opening_inv = 0.0
            inv_comp = ProjectCostComponent(
                component_id="opening_inventory",
                name="Opening Stock & Raw Materials",
                amount=0.0,
                unit="INR",
                source_type="CALCULATED",
                source_id="NON_RETAIL_ARCHETYPE_RULE",
                confidence=1.0,
                calculation_method="archetype_non_inventory_rule",
                status="RESOLVED",
                explanation=f"{archetype.value} operational cycle provisions working capital via operational buffer rather than retail shelf stock."
            )
        elif wc_analysis.total_working_capital is not None:
            opening_inv = 0.0
            inv_comp = ProjectCostComponent(
                component_id="opening_inventory",
                name="Opening Stock & Raw Materials",
                amount=0.0,
                unit="INR",
                source_type="DERIVED",
                source_id="INTEGRATED_WORKING_CAPITAL",
                confidence=wc_analysis.confidence,
                calculation_method="subsumed_in_working_capital_buffer",
                status="RESOLVED",
                explanation="Opening materials subsumed within working capital buffer."
            )
        else:
            opening_inv = None
            inv_comp = ProjectCostComponent(
                component_id="opening_inventory",
                name="Opening Stock & Raw Materials",
                amount=None,
                unit="INR",
                source_type="UNKNOWN",
                source_id=None,
                confidence=0.0,
                status="UNKNOWN",
                explanation="Opening inventory requirement is unknown and requires entrepreneur clarification."
            )

        components.append(inv_comp)
        if opening_inv is not None:
            confidences.append(inv_comp.confidence)
            provenance_list.append(inv_comp.provenance or {
                "source_type": inv_comp.source_type,
                "source_id": inv_comp.source_id or "OPENING_INV",
                "description": f"Opening inventory ₹{opening_inv:,.2f}",
                "confidence": inv_comp.confidence
            })

        # ---------------------------------------------------------------------
        # 4. Working Capital Component (Buffer & Receivables less Payables)
        # Note: In project cost financing, if opening inventory is funded separately
        # as a distinct component, WC component represents the non-inventory WC buffer.
        # ---------------------------------------------------------------------
        effective_wc_component: Optional[float] = None
        wc_comp: Optional[ProjectCostComponent] = None
        total_wc_val: Optional[float] = wc_analysis.total_working_capital

        if wc_analysis.total_working_capital is not None:
            # If opening inventory was treated as a separate line item above:
            if opening_inv is not None and opening_inv > 0 and wc_analysis.inventory_requirement:
                # Non-inventory working capital buffer covers cash buffer + receivables - payables
                non_inv_wc = round(
                    max(0.0, (wc_analysis.operating_cash_buffer or 0.0) +
                        (wc_analysis.receivable_requirement or 0.0) -
                        (wc_analysis.payable_credit or 0.0)), 2
                )
                effective_wc_component = non_inv_wc
            else:
                effective_wc_component = wc_analysis.total_working_capital

            wc_comp = ProjectCostComponent(
                component_id="operating_buffer",
                name="Additional Operating Buffer & Receivables",
                amount=effective_wc_component,
                unit="INR",
                source_type=wc_analysis.methodology,
                source_id="WORKING_CAPITAL_ENGINE",
                confidence=wc_analysis.confidence,
                calculation_method=wc_analysis.notes,
                provenance={
                    "source_type": "CALCULATED",
                    "source_id": "WORKING_CAPITAL_ENGINE",
                    "description": f"Operating buffer component ₹{effective_wc_component:,.2f}",
                    "confidence": wc_analysis.confidence
                },
                status=wc_analysis.status,
                explanation=f"Working capital allocation for operating buffer and receivables."
            )
            confidences.append(wc_analysis.confidence)
        else:
            effective_wc_component = None
            wc_comp = ProjectCostComponent(
                component_id="operating_buffer",
                name="Additional Operating Buffer & Receivables",
                amount=None,
                unit="INR",
                source_type="UNKNOWN",
                source_id=None,
                confidence=0.0,
                status="UNKNOWN",
                explanation="Working capital requirement could not be calculated from current drivers."
            )

        components.append(wc_comp)

        # ---------------------------------------------------------------------
        # 5. Fixed Capital / CapEx Component
        # ---------------------------------------------------------------------
        capex_decomp = self.capex_engine.decompose(
            archetype=archetype,
            benchmark_data=benchmark_data,
            capex_override=user_inputs.get("capex_override"),
            user_inputs=user_inputs,
            total_project_cost=scheme_financeable_cost or preferred_project_cost,
        )
        effective_capex = capex_decomp.total_capex

        if effective_capex is not None:
            capex_comp = ProjectCostComponent(
                component_id="capex",
                name="Fixed Capital / CapEx",
                amount=effective_capex,
                unit="INR",
                source_type=capex_decomp.source,
                source_id=f"CAPEX_ENGINE_{capex_decomp.source}",
                confidence=capex_decomp.confidence,
                calculation_method="category_decomposition",
                provenance={
                    "source_type": capex_decomp.source,
                    "source_id": "CAPEX_ENGINE",
                    "description": f"Fixed capital ₹{effective_capex:,.2f} decomposed across setup, equipment, tools",
                    "confidence": capex_decomp.confidence
                },
                status="RESOLVED" if capex_decomp.source == "USER_SPECIFIED" else "BENCHMARKED",
                explanation=f"Fixed capital investment derived via {capex_decomp.source}."
            )
            confidences.append(capex_decomp.confidence)
        else:
            capex_comp = ProjectCostComponent(
                component_id="capex",
                name="Fixed Capital / CapEx",
                amount=None,
                unit="INR",
                source_type="UNKNOWN",
                source_id=None,
                confidence=0.0,
                status="UNKNOWN",
                explanation="CapEx requirement is unknown and requires equipment quotation or benchmark."
            )

        components.append(capex_comp)

        # ---------------------------------------------------------------------
        # 6. Pre-operative / Setup Expenses
        # Check benchmark capex.pre_operative_pct or explicit user input
        # ---------------------------------------------------------------------
        pre_op_amount: Optional[float] = None
        pre_op_source = "UNKNOWN"
        pre_op_conf = 0.0
        pre_op_status = "UNKNOWN"
        pre_op_expl = "No benchmark or user evidence available for pre-operative setup costs."

        raw_bm_data = benchmark_data if isinstance(benchmark_data, dict) else (
            benchmark_data.model_dump() if benchmark_data and hasattr(benchmark_data, "model_dump") else {}
        )
        bm_capex = raw_bm_data.get("capex", {}) if isinstance(raw_bm_data, dict) else {}
        pre_op_pct = float(bm_capex.get("pre_operative_pct") or 0.0)

        if user_inputs.get("pre_operating_cost") is not None:
            pre_op_amount = round(float(user_inputs["pre_operating_cost"]), 2)
            pre_op_source = "USER_SPECIFIED"
            pre_op_conf = 1.0
            pre_op_status = "RESOLVED"
            pre_op_expl = f"Pre-operative setup expenses specified directly by user: ₹{pre_op_amount:,.2f}."
        elif pre_op_pct > 0 and effective_capex is not None and effective_capex > 0:
            pre_op_amount = round(effective_capex * (pre_op_pct / 100.0), 2)
            pre_op_source = "BENCHMARK_DERIVED"
            pre_op_conf = 0.85
            pre_op_status = "BENCHMARKED"
            pre_op_expl = f"Benchmark pre-operative allowance ({pre_op_pct}% of CapEx): ₹{pre_op_amount:,.2f}."
        else:
            pre_op_amount = None
            pre_op_source = "UNKNOWN"
            pre_op_conf = 0.0
            pre_op_status = "UNKNOWN"
            pre_op_expl = "Pre-operative setup expenses unknown (no benchmark or user evidence)."

        pre_op_comp = ProjectCostComponent(
            component_id="pre_operating_cost",
            name="Pre-operative & Setup Costs",
            amount=pre_op_amount,
            unit="INR",
            source_type=pre_op_source,
            source_id="PRE_OPERATIVE_MODULE" if pre_op_amount is not None else None,
            confidence=pre_op_conf,
            calculation_method=f"pre_op_{pre_op_source.lower()}" if pre_op_amount is not None else None,
            provenance={
                "source_type": pre_op_source,
                "source_id": "PRE_OPERATIVE_SETUP",
                "description": f"Pre-operative costs provision: ₹{pre_op_amount:,.2f}" if pre_op_amount is not None else "Pre-operative costs unknown",
                "confidence": pre_op_conf
            } if pre_op_amount is not None else None,
            status=pre_op_status,
            explanation=pre_op_expl
        )
        components.append(pre_op_comp)
        if pre_op_amount is not None:
            confidences.append(pre_op_conf)

        # ---------------------------------------------------------------------
        # 7. Supported Contingency ONLY when explicitly justified
        # Rule: Contingency is NEVER invented. Only included if benchmark explicitly
        # provisions for civil/plant contingencies or user specifies a reserve.
        # ---------------------------------------------------------------------
        contingency_amount: Optional[float] = None
        contingency_pct = float(bm_capex.get("contingency_pct") or 0.0)

        if user_inputs.get("contingency") is not None:
            contingency_amount = round(float(user_inputs["contingency"]), 2)
            cont_source = "USER_SPECIFIED"
            cont_conf = 1.0
            cont_status = "RESOLVED"
            cont_expl = f"Contingency reserve specified directly by user: ₹{contingency_amount:,.2f}."
        elif contingency_pct > 0 and effective_capex is not None and effective_capex > 0:
            contingency_amount = round(effective_capex * (contingency_pct / 100.0), 2)
            cont_source = "BENCHMARK_DERIVED"
            cont_conf = 0.80
            cont_status = "BENCHMARKED"
            cont_expl = f"Benchmark contingency provision ({contingency_pct}% of CapEx): ₹{contingency_amount:,.2f}."
        else:
            contingency_amount = None
            cont_source = "UNKNOWN"
            cont_conf = 0.0
            cont_status = "UNKNOWN"
            cont_expl = "Contingency reserve unknown (no benchmark or user provision)."

        cont_comp = ProjectCostComponent(
            component_id="contingency",
            name="Contingency Reserve",
            amount=contingency_amount,
            unit="INR",
            source_type=cont_source,
            source_id="CONTINGENCY_POLICY" if contingency_amount is not None else None,
            confidence=cont_conf,
            calculation_method="explicit_benchmark_contingency" if contingency_amount is not None else None,
            provenance={
                "source_type": cont_source,
                "source_id": "CONTINGENCY_POLICY",
                "description": f"Contingency provision: ₹{contingency_amount:,.2f}" if contingency_amount is not None else "Contingency unknown",
                "confidence": cont_conf
            } if contingency_amount is not None else None,
            status=cont_status,
            explanation=cont_expl
        )
        components.append(cont_comp)
        if contingency_amount is not None:
            confidences.append(cont_conf)

        # ---------------------------------------------------------------------
        # 8. Reconcile Total Calculated Project Cost
        # Total = CapEx + Opening Inventory + Working Capital + Pre-operative (if resolved) + Contingency (if resolved)
        # ---------------------------------------------------------------------
        known_elements = [effective_capex, opening_inv, effective_wc_component]
        is_partially_derived = any(c.source_type == "CALCULATED" or c.status == "PARTIALLY_DERIVED" for c in components)
        
        calculated_total: Optional[float] = None
        if any(e is None for e in known_elements):
            status = "INSUFFICIENT_DATA"
            calculated_total = None
            avg_confidence = 0.0
        else:
            # If pre-operative cost or contingency was derived from benchmark capex breakdown (BENCHMARK_DERIVED),
            # it is already an internal allocation of effective_capex (capex breakdown pcts sum to 100%).
            # Adding it again would double-count. It is only additive if specified directly by user (USER_SPECIFIED).
            add_pre_op = pre_op_amount if (pre_op_amount is not None and pre_op_source == "USER_SPECIFIED") else 0.0
            add_cont = contingency_amount if (contingency_amount is not None and cont_source == "USER_SPECIFIED") else 0.0

            calculated_total = round(
                (effective_capex or 0.0) +
                (opening_inv or 0.0) +
                (effective_wc_component or 0.0) +
                add_pre_op +
                add_cont, 2
            )
            status = "RESOLVED"
            avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.80

        # ---------------------------------------------------------------------
        # 9. Promoter Margin & Debt Financing Split
        # ---------------------------------------------------------------------
        promoter_margin: Optional[float] = None
        debt_component: Optional[float] = None

        if calculated_total is not None and calculated_total > 0:
            promoter_margin = round(calculated_total * scheme_margin_ratio, 2)
            debt_component = round(calculated_total - promoter_margin, 2)

        # ---------------------------------------------------------------------
        # 10. Project Cost Reconciliation against Scheme & User requests
        # ---------------------------------------------------------------------
        reconciliation = self.reconciler.reconcile(
            calculated_project_cost=calculated_total,
            scheme_financeable_project_cost=scheme_financeable_cost,
            user_requested_project_cost=preferred_project_cost,
            promoter_margin=promoter_margin,
            debt_component=debt_component,
            is_partially_derived=is_partially_derived,
        )

        project_cost_analysis = ProjectCostAnalysis(
            status=status,
            total_project_cost=calculated_total,
            capex=effective_capex,
            opening_inventory=opening_inv,
            working_capital=effective_wc_component,
            pre_operating_cost=pre_op_amount,
            contingency=contingency_amount,
            promoter_margin=promoter_margin,
            debt_component=debt_component,
            unexplained_amount=reconciliation.unexplained_amount,
            capex_decomposition=capex_decomp,
            reconciliation=reconciliation,
            components=components,
            provenance=provenance_list,
            confidence=avg_confidence
        )

        return project_cost_analysis, wc_analysis, derived_assumptions


# Global singleton
project_cost_engine = ProjectCostEngine()
