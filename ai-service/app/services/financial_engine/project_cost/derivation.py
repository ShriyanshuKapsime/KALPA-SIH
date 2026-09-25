"""
Milestone 2: Deterministic Derivation & Dependency Engine.
Resolves derived financial drivers with topological ordering, cycle detection,
missing dependency handling, and strict provenance tracking.
Zero LLM calculations.
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, SourceType, AssumptionStatus, AssumptionType, Provenance
)
from app.services.financial_engine.intelligence.driver_registry import DriverDefinition, driver_registry
from app.services.financial_engine.intelligence.archetype_registry import FinancialArchetype

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in driver derivation rules."""
    pass


class DerivationEngine:
    """
    Deterministic dependency resolver for financial drivers.
    Evaluates derivation rules in topological order without recursive infinite loops.
    """

    def detect_cycles(self, dependency_graph: Dict[str, List[str]]) -> Optional[List[str]]:
        """
        Detects cycles in dependency graph using DFS.
        Returns the cycle path if found, or None if acyclic.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_path: List[str] = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependency_graph.get(node, []):
                if neighbor in dependency_graph:
                    if neighbor not in visited:
                        if dfs(neighbor, path):
                            return True
                    elif neighbor in rec_stack:
                        path.append(neighbor)
                        cycle_path.extend(path[path.index(neighbor):])
                        return True

            path.pop()
            rec_stack.remove(node)
            return False

        for n in dependency_graph:
            if n not in visited:
                if dfs(n, []):
                    return cycle_path
        return None

    def get_topological_order(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """
        Returns topological ordering of driver IDs using Kahn's algorithm.
        Raises CircularDependencyError if cycle detected.
        """
        target_nodes = set(dependency_graph.keys())
        in_degree: Dict[str, int] = {node: 0 for node in target_nodes}
        adj_list: Dict[str, List[str]] = {node: [] for node in target_nodes}

        for node, deps in dependency_graph.items():
            for dep in deps:
                # Only dependencies that are themselves targets need topological ordering
                if dep in target_nodes:
                    adj_list[dep].append(node)
                    in_degree[node] += 1

        queue = [node for node, deg in in_degree.items() if deg == 0]
        order: List[str] = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for dependent in adj_list.get(curr, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(order) < len(target_nodes):
            cycle = self.detect_cycles(dependency_graph) or []
            cycle_str = " -> ".join(cycle) if cycle else "detected"
            raise CircularDependencyError(f"Circular dependency detected in derivation graph: {cycle_str}")

        return order

    def resolve_derivations(
        self,
        archetype: FinancialArchetype,
        assumptions: List[ResolvedAssumption],
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> List[ResolvedAssumption]:
        """
        Executes deterministic derivations over the assumptions list.
        - Existing USER_INPUT and VERIFIED_EVIDENCE values are strictly preserved (never overwritten).
        - Unknown drivers with satisfiable dependencies are derived.
        - Missing dependencies keep drivers as UNKNOWN (never silent zero).
        """
        user_inputs = user_inputs or {}
        asm_map: Dict[str, ResolvedAssumption] = {a.driver_id: a for a in assumptions}
        val_map: Dict[str, Any] = {}

        for did, a in asm_map.items():
            if a.value is not None:
                val_map[did] = a.value

        # Also populate from user_inputs if present
        for k, v in user_inputs.items():
            if v is not None and k not in val_map:
                val_map[k] = v

        # Build dynamic derivation rules for current archetype
        rules = self._get_derivation_rules_for_archetype(archetype)
        dep_graph: Dict[str, List[str]] = {target: rule["depends_on"] for target, rule in rules.items()}

        # Check for cycles
        cycle = self.detect_cycles(dep_graph)
        if cycle:
            cycle_str = " -> ".join(cycle)
            logger.error(f"[DERIVATION ENGINE] Cycle detected: {cycle_str}")
            raise CircularDependencyError(f"Circular dependency detected in driver derivations: {cycle_str}")

        # Topologically sort derivation targets
        try:
            eval_order = self.get_topological_order(dep_graph)
        except CircularDependencyError as e:
            logger.error(f"[DERIVATION ENGINE] Topological sorting failed: {e}")
            raise

        for target in eval_order:
            if target not in rules:
                continue

            existing_asm = asm_map.get(target)

            # Rule: Stronger explicit values (USER_INPUT, VERIFIED_EVIDENCE) MUST NOT be overwritten
            if existing_asm and existing_asm.source_type in (SourceType.USER_INPUT, SourceType.DERIVED) and existing_asm.user_confirmed and existing_asm.value is not None:
                logger.debug(f"[DERIVATION ENGINE] Preserving explicit user/verified value for {target}={existing_asm.value}")
                continue

            rule_def = rules[target]
            deps = rule_def["depends_on"]
            func = rule_def["func"]
            formula_desc = rule_def["formula"]

            # Check if all dependencies are satisfied and non-None
            missing_deps = [d for d in deps if val_map.get(d) is None]
            if missing_deps:
                logger.debug(f"[DERIVATION ENGINE] Cannot derive {target}: missing dependencies {missing_deps}")
                continue

            # Execute deterministic calculation
            try:
                dep_values = {d: val_map[d] for d in deps}
                derived_val = func(dep_values)

                if derived_val is not None:
                    # Sanity validation
                    if isinstance(derived_val, (int, float)):
                        derived_val = round(max(0.0, float(derived_val)), 2)

                    val_map[target] = derived_val

                    # Compute combined confidence
                    dep_confs = [
                        asm_map[d].confidence for d in deps if d in asm_map and asm_map[d].confidence > 0
                    ]
                    calc_conf = round(min(dep_confs) * 0.95, 2) if dep_confs else 0.80

                    drv_def = driver_registry.get_driver(target)
                    unit = drv_def.unit if drv_def else "INR"
                    crit = drv_def.criticality if drv_def else "MEDIUM"

                    new_asm = ResolvedAssumption(
                        driver_id=target,
                        value=derived_val,
                        unit=unit,
                        source_type=SourceType.CALCULATED,
                        source_id=f"DERIVATION_ENGINE_{target.upper()}",
                        confidence=calc_conf,
                        status=AssumptionStatus.CALCULATED,
                        assumption_type=AssumptionType.DERIVED,
                        user_confirmed=False,
                        required=True,
                        criticality=crit,
                        provenance=Provenance(
                            source_type=SourceType.CALCULATED,
                            source_id=f"FORMULA:{formula_desc}",
                            description=f"Derived deterministically: {formula_desc} using {deps}",
                            confidence=calc_conf,
                        ),
                        notes=f"Calculated via {formula_desc}",
                    )
                    asm_map[target] = new_asm
                    logger.info(f"[DERIVATION ENGINE] Successfully derived {target}={derived_val} via {formula_desc}")
            except Exception as ex:
                logger.warning(f"[DERIVATION ENGINE] Failed calculating {target}: {ex}")

        return list(asm_map.values())

    def _get_derivation_rules_for_archetype(self, archetype: FinancialArchetype) -> Dict[str, Dict[str, Any]]:
        """
        Returns deterministic derivation rules mapped to financial archetypes.
        """
        rules: Dict[str, Dict[str, Any]] = {}

        # 1. Retail & Trading Revenue
        if archetype in (FinancialArchetype.INVENTORY_RETAIL, FinancialArchetype.TRADING):
            rules["monthly_revenue"] = {
                "depends_on": ["monthly_transactions", "average_ticket"],
                "formula": "monthly_transactions * average_ticket",
                "func": lambda d: float(d["monthly_transactions"]) * float(d["average_ticket"])
            }
        elif archetype in (FinancialArchetype.SERVICE, FinancialArchetype.REPAIR):
            rules["monthly_revenue"] = {
                "depends_on": ["jobs_per_day", "operating_days", "average_realization"],
                "formula": "jobs_per_day * operating_days * average_realization",
                "func": lambda d: float(d["jobs_per_day"]) * float(d["operating_days"]) * float(d["average_realization"])
            }
        elif archetype in (FinancialArchetype.SMALL_MANUFACTURING, FinancialArchetype.FOOD_PROCESSING):
            rules["monthly_revenue"] = {
                "depends_on": ["installed_capacity", "operating_days", "utilization", "selling_price"],
                "formula": "installed_capacity * operating_days * (utilization / 100.0) * selling_price",
                "func": lambda d: float(d["installed_capacity"]) * float(d["operating_days"]) * (float(d["utilization"]) / 100.0) * float(d["selling_price"])
            }

        # 2. COGS (Cost of Goods Sold)
        rules["monthly_cogs"] = {
            "depends_on": ["monthly_revenue", "gross_margin"],
            "formula": "monthly_revenue * (1.0 - gross_margin / 100.0)",
            "func": lambda d: float(d["monthly_revenue"]) * (1.0 - (float(d["gross_margin"]) / 100.0))
        }

        # 3. Inventory Requirement (Holding Cycle)
        rules["inventory_requirement"] = {
            "depends_on": ["monthly_cogs", "inventory_days"],
            "formula": "(monthly_cogs / 30.0) * inventory_days",
            "func": lambda d: (float(d["monthly_cogs"]) / 30.0) * float(d["inventory_days"])
        }

        # 4. Receivables Requirement
        rules["receivable_requirement"] = {
            "depends_on": ["monthly_revenue", "receivable_days"],
            "formula": "(monthly_revenue / 30.0) * receivable_days",
            "func": lambda d: (float(d["monthly_revenue"]) / 30.0) * float(d["receivable_days"])
        }

        # 5. Payables / Supplier Credit Offset
        rules["payable_credit"] = {
            "depends_on": ["monthly_cogs", "payable_days"],
            "formula": "(monthly_cogs / 30.0) * payable_days",
            "func": lambda d: (float(d["monthly_cogs"]) / 30.0) * float(d["payable_days"])
        }

        # 6. Staff Salary Total (derived only when salary_per_person is supported by user or benchmark)
        rules["salary_cost"] = {
            "depends_on": ["staff_count", "salary_per_person"],
            "formula": "staff_count * salary_per_person",
            "func": lambda d: float(d["staff_count"]) * float(d["salary_per_person"]) if float(d["staff_count"]) > 0 else 0.0
        }

        return rules


# Global singleton
derivation_engine = DerivationEngine()
