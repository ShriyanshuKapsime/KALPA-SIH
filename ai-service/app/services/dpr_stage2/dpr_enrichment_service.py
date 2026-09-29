"""
Stage 14.2: DPR Enrichment & Deterministic Inference Service.
Main orchestrator for KALPA Stage 14.2. Ingests Stage 14.1 handoff package,
executes deterministic resolvers, triggers M1-M6 financial calculations,
populates canonical 39 sections, compiles Assumption Review cards, and persists enriched package.
"""
import os
import json
import copy
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.dpr_stage1 import (
    dpr_context_builder,
    dpr_gap_analyzer,
    dpr_scenario_manager,
    build_stage14_handoff_package,
    DPRStage14HandoffPackage,
    normalize_field_id,
    get_field_definition,
    DPR_STATE_ISOLATION_ERROR,
    is_business_concept_match,
)
from app.services.dpr_stage2.dpr_enrichment_schemas import (
    DPREnrichmentPackage,
    EnrichmentField,
    EnrichmentSourceType,
    DerivationMethod,
    AssumptionReviewItem,
    AssumptionReviewAction,
    AssumptionReviewPackage,
    ValidationCheckResult,
    EnrichmentValidationSummary,
)
from app.services.dpr_stage2.evidence_resolver import evidence_resolver
from app.services.dpr_stage2.benchmark_resolver import benchmark_resolver
from app.services.dpr_stage2.market_resolver import market_resolver
from app.services.dpr_stage2.policy_scheme_resolver import policy_scheme_resolver
from app.services.dpr_stage2.deterministic_inference_engine import deterministic_inference_engine
from app.services.dpr_stage2.dpr_enrichment_validator import dpr_enrichment_validator

logger = logging.getLogger(__name__)

# Persistent Enrichment Storage Directory
ENRICHMENT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../data/dpr_enrichment")
)
os.makedirs(ENRICHMENT_DIR, exist_ok=True)


class DPREnrichmentService:
    """
    Coordinates Stage 14.2 DPR Enrichment & Deterministic Inference.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or ENRICHMENT_DIR
        self._cache: Dict[str, DPREnrichmentPackage] = {}
        os.makedirs(self.storage_dir, exist_ok=True)

    def _file_path(self, business_id: str, scenario_id: str) -> str:
        b_id = (business_id or "").strip()
        s_id = (scenario_id or "").strip()
        safe_biz = "".join(c for c in b_id if c.isalnum() or c in ("-", "_"))
        safe_scen = "".join(c for c in s_id if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.storage_dir, f"{safe_biz}__{safe_scen}__enrichment.json")

    def invalidate_enrichment(self, business_id: str, scenario_id: Optional[str] = None):
        """Invalidates in-memory and disk cached enrichment for the given business & scenario."""
        b_id = (business_id or "").strip()
        s_id = scenario_id.strip() if scenario_id else f"DPR-{b_id[:8] if len(b_id) >= 8 else b_id}"
        cache_key = f"{b_id}:{s_id}"
        self._cache.pop(cache_key, None)
        fp = self._file_path(b_id, s_id)
        if os.path.exists(fp):
            try:
                os.remove(fp)
                logger.info(f"[DPREnrichmentService] Evicted stale enrichment file: {fp}")
            except Exception as e:
                logger.warning(f"[DPREnrichmentService] Could not remove stale enrichment file {fp}: {e}")

    def get_persisted_enrichment(self, business_id: str, scenario_id: Optional[str] = None) -> Optional[DPREnrichmentPackage]:
        business_id = (business_id or "").strip()
        if scenario_id:
            scenario_id = scenario_id.strip()
        s_id = scenario_id or f"DPR-{business_id[:8] if len(business_id) >= 8 else business_id}"
        s_id = s_id.strip()
        
        # Cross-business scenario mismatch protection
        if scenario_id and scenario_id.startswith("DPR-"):
            clean_biz = business_id.replace("-", "").replace("_", "").lower()
            clean_scen = scenario_id.replace("DPR-", "").replace("-", "").replace("_", "").lower()
            if clean_biz.startswith("test") and clean_scen.startswith("test"):
                cb_check = clean_biz[4:]
                cs_check = clean_scen[4:]
            else:
                cb_check = clean_biz
                cs_check = clean_scen
            if cb_check and cs_check and len(cs_check) >= 3 and len(cb_check) >= 3:
                if not cb_check.startswith(cs_check[:3]) and not cs_check.startswith(cb_check[:3]):
                    raise DPR_STATE_ISOLATION_ERROR(f"Scenario '{scenario_id}' does not belong to business '{business_id}'")

        cache_key = f"{business_id}:{s_id}"

        # 1. In-memory check
        if cache_key in self._cache:
            pkg = self._cache[cache_key]
            if pkg.business_id.strip().lower() != business_id.lower():
                self._cache.pop(cache_key, None)
                raise DPR_STATE_ISOLATION_ERROR(f"requested_business_id={business_id} returned_business_id={pkg.business_id}")
            if pkg.scenario_id.strip().lower() != s_id.lower():
                self._cache.pop(cache_key, None)
                raise DPR_STATE_ISOLATION_ERROR(f"requested_scenario_id={s_id} returned_scenario_id={pkg.scenario_id}")

            # Cross-scenario field contamination check
            flds = pkg.fields if hasattr(pkg, "fields") else {}
            title_fld = flds.get("dpr_title")
            title_val = title_fld.value if hasattr(title_fld, "value") else (title_fld.get("value") if isinstance(title_fld, dict) else "")
            if title_val and not is_business_concept_match(business_id, str(title_val)):
                logger.error(f"[DPR_CROSS_SCENARIO_DATA_ERROR] field=dpr_title requested_business_id={business_id} cached_title={title_val}. Invalidating in-memory enrichment.")
                self._cache.pop(cache_key, None)
                pkg = None

            if pkg:
                scen = dpr_scenario_manager.get_or_create_scenario(business_id, s_id)
                if scen and scen.version > pkg.version:
                    logger.info(f"[DPREnrichmentService] In-memory enrichment stale (pkg v{pkg.version} < scen v{scen.version}) for {cache_key}. Invalidating.")
                    self._cache.pop(cache_key, None)
                elif pkg.metadata.get("status") == "BLOCKED" and scen and len(scen.user_answers) > 0:
                    logger.info(f"[DPREnrichmentService] In-memory enrichment previously BLOCKED but answers exist for {cache_key}. Invalidating.")
                    self._cache.pop(cache_key, None)
                else:
                    return pkg

        # 2. Disk persistence check
        fp = self._file_path(business_id, s_id)
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                pkg_biz = data.get("business_id", "").strip() if isinstance(data.get("business_id"), str) else data.get("business_id")
                pkg_scen = data.get("scenario_id", "").strip() if isinstance(data.get("scenario_id"), str) else data.get("scenario_id")
                if pkg_biz.lower() != business_id.lower():
                    raise DPR_STATE_ISOLATION_ERROR(f"requested_business_id={business_id} returned_business_id={pkg_biz}")
                if pkg_scen and pkg_scen.lower() != s_id.lower():
                    raise DPR_STATE_ISOLATION_ERROR(f"requested_scenario_id={s_id} returned_scenario_id={pkg_scen}")

                # Contamination check on disk data
                title_val = data.get("fields", {}).get("dpr_title", {}).get("value")
                if title_val and not is_business_concept_match(business_id, str(title_val)):
                    logger.error(f"[DPR_CROSS_SCENARIO_DATA_ERROR] field=dpr_title requested_business_id={business_id} disk_title={title_val}. Evicting contaminated disk file.")
                    self.invalidate_enrichment(business_id, s_id)
                    return None

                scen = dpr_scenario_manager.get_or_create_scenario(business_id, s_id)
                pkg_ver = data.get("version", 1)
                if scen and scen.version > pkg_ver:
                    logger.info(f"[DPREnrichmentService] Disk enrichment stale (pkg v{pkg_ver} < scen v{scen.version}) for {cache_key}. Refreshing.")
                    return None
                if data.get("metadata", {}).get("status") == "BLOCKED" and scen and len(scen.user_answers) > 0:
                    logger.info(f"[DPREnrichmentService] Disk enrichment previously BLOCKED but answers exist for {cache_key}. Refreshing.")
                    return None

                data["business_id"] = pkg_biz
                if pkg_scen:
                    data["scenario_id"] = pkg_scen
                pkg = DPREnrichmentPackage(**data)
                self._cache[cache_key] = pkg
                return pkg
            except (ValueError, DPR_STATE_ISOLATION_ERROR):
                raise
            except Exception as e:
                logger.error(f"[DPREnrichmentService] Failed reading persisted enrichment {fp}: {e}")

        return None

    def save_enrichment(self, pkg: DPREnrichmentPackage) -> DPREnrichmentPackage:
        if not pkg.business_id:
            raise ValueError("DPR_STATE_ISOLATION_ERROR: Cannot save enrichment package without business_id")
        pkg.business_id = pkg.business_id.strip()
        pkg.scenario_id = pkg.scenario_id.strip()
        cache_key = f"{pkg.business_id}:{pkg.scenario_id}"
        self._cache[cache_key] = pkg

        fp = self._file_path(pkg.business_id, pkg.scenario_id)
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(pkg.model_dump(), f, indent=2)
        except Exception as e:
            logger.error(f"[DPREnrichmentService] Failed persisting enrichment {fp}: {e}")

        return pkg

    async def run_enrichment(
        self,
        business_id: str,
        scenario_id: Optional[str] = None,
        db: Optional[Session] = None,
        handoff_package_override: Optional[DPRStage14HandoffPackage] = None,
    ) -> DPREnrichmentPackage:
        """
        Executes Stage 14.2 DPR Enrichment & Deterministic Inference.
        1. Loads Stage 14.1 handoff package.
        2. Verifies READY_FOR_STAGE_14_2 gate (hard stop if not ready).
        3. Executes Evidence, Benchmark, Market, and Policy resolvers.
        4. Runs DeterministicInferenceEngine (orchestrating M1-M6).
        5. Compiles AssumptionReviewPackage.
        6. Validates enrichment.
        7. Persists Stage 14.2 package.
        """
        scen_state = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        active_scenario_id = scen_state.scenario_id

        # 1. Obtain Stage 14.1 Handoff Package
        if handoff_package_override:
            handoff = handoff_package_override
        else:
            ctx_pkg = await dpr_context_builder.build_context(
                business_id=business_id,
                db=db,
                scenario_id=active_scenario_id,
                user_overrides=scen_state.user_overrides,
                user_answers=scen_state.user_answers,
                accepted_benchmarks=scen_state.accepted_benchmarks,
                document_statuses=scen_state.document_statuses
            )
            gap_res = dpr_gap_analyzer.analyze(ctx_pkg)
            handoff = build_stage14_handoff_package(
                business_id=business_id,
                context=ctx_pkg,
                gap_analysis=gap_res,
                scenario_id=active_scenario_id
            )

        intake_dict = handoff.model_dump()

        # 2. Gate Verification - HARD STOP if not ready for Stage 14.2
        if not handoff.readiness.is_ready_for_stage_14_2:
            logger.warning(f"[DPREnrichmentService] Stage 14.1 handoff blocked for {business_id}: {handoff.readiness.reasons}")
            blocked_pkg = DPREnrichmentPackage(
                metadata={
                    "stage": "STAGE_14_2_DPR_ENRICHMENT_INFERENCE",
                    "business_id": business_id,
                    "scenario_id": active_scenario_id,
                    "version": scen_state.version,
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "14.2.0-FROZEN",
                    "status": "BLOCKED",
                    "blocking_reasons": handoff.readiness.reasons,
                },
                business_id=business_id,
                scenario_id=active_scenario_id,
                version=scen_state.version,
                intake_package_snapshot=intake_dict,
                business_profile=intake_dict.get("existing_business_profile") or {},
                entrepreneur_profile=intake_dict.get("entrepreneur_context") or {},
                location_profile=intake_dict.get("location_context") or {},
                market_intelligence=intake_dict.get("market_context") or {},
                scheme_policy_context=intake_dict.get("scheme_context") or {},
                financial_package=intake_dict.get("financial_package") or {},
                risk_assessment=intake_dict.get("risk_context") or {},
                feasibility_synthesis=intake_dict.get("feasibility_context") or {},
                swot_matrix=intake_dict.get("swot_context") or {},
                documents=intake_dict.get("documents") or {},
                modules={},
                sections={},
                fields={},
                assumption_review=AssumptionReviewPackage(
                    business_id=business_id,
                    scenario_id=active_scenario_id,
                    version=scen_state.version,
                    total_assumptions=0,
                    user_confirmed_count=0,
                    user_overridden_count=0,
                    assumptions_requiring_review=[],
                    informational_assumptions=[],
                ),
                validation=EnrichmentValidationSummary(
                    overall_valid=False,
                    total_checks=1,
                    passed_checks=0,
                    failed_checks=1,
                    warnings_count=0,
                    checks=[
                        ValidationCheckResult(
                            check_id="CHK_INTAKE_READINESS",
                            rule_name="Stage 14.1 Intake Gate Verified",
                            passed=False,
                            severity="CRITICAL",
                            details=f"Stage 14.1 verified intake handoff package is not ready for enrichment: {', '.join(handoff.readiness.reasons)}",
                            affected_fields=["business_name", "promoter_name", "location_state", "location_district"]
                        )
                    ],
                    blocking_reasons=handoff.readiness.reasons,
                ),
                is_enrichment_complete=False,
                can_proceed_to_validation=False
            )
            return self.save_enrichment(blocked_pkg)

        b_class = intake_dict.get("business_classification", {})
        cat_str = b_class.get("archetype")
        nic_str = b_class.get("nic_code")

        # 3. Execute Resolvers
        # 3.1 Evidence Resolver
        evidence_fields = evidence_resolver.resolve_evidence(
            documents=intake_dict.get("documents", {}),
            existing_fields=intake_dict.get("fields", {})
        )

        # 3.2 Benchmark Resolver
        benchmark_fields = benchmark_resolver.resolve_benchmarks(
            business_id=business_id,
            category=cat_str,
            nic_code=nic_str,
            user_overrides=scen_state.user_overrides,
            accepted_benchmarks=scen_state.accepted_benchmarks
        )

        # 3.3 Market Resolver
        market_fields = market_resolver.resolve_market_evidence(
            market_context=intake_dict.get("market_context"),
            opportunity_context=intake_dict.get("opportunity_context")
        )

        # 3.4 Policy / Scheme Resolver
        p_cost_approx = intake_dict.get("fields", {}).get("total_project_cost", {}).get("value")
        policy_fields = policy_scheme_resolver.resolve_policy_rules(
            scheme_context=intake_dict.get("scheme_context"),
            entrepreneur_profile=intake_dict.get("entrepreneur_context"),
            location_profile=intake_dict.get("location_context"),
            project_cost=float(p_cost_approx) if p_cost_approx else None
        )

        # 4. Run Deterministic Inference Engine (with M1-M6)
        inferred = deterministic_inference_engine.infer_dpr_context(
            business_id=business_id,
            scenario_id=active_scenario_id,
            intake_package=intake_dict,
            evidence_fields=evidence_fields,
            benchmark_fields=benchmark_fields,
            market_fields=market_fields,
            policy_fields=policy_fields
        )

        fields_dict: Dict[str, EnrichmentField] = inferred["fields"]
        sec_summaries = inferred["sections"]
        mod_summaries = inferred["modules"]
        fin_pkg = inferred["financial_package"]

        # 5. Compile Assumption Review Package ("Confirm KALPA's Assumptions")
        assumption_review = self._build_assumption_review(
            business_id=business_id,
            scenario_id=active_scenario_id,
            version=scen_state.version,
            fields=fields_dict,
            benchmark_fields=benchmark_fields,
            user_overrides=scen_state.user_overrides
        )

        # 6. Validate Enriched Context
        validation_res = dpr_enrichment_validator.validate_enrichment(
            fields=fields_dict,
            financial_package=fin_pkg,
            intake_package=intake_dict,
            scenario_id=active_scenario_id
        )

        # 7. Package and Persist
        is_complete = validation_res.overall_valid and handoff.readiness.is_ready_for_stage_14_2

        prov_dict = {
            fid: {
                "source_type": str(f.source_type.value if hasattr(f.source_type, "value") else f.source_type),
                "source_id": f.source_id,
                "source_reference": f.source_reference,
                "confidence": f.confidence,
                "derivation_method": str(f.derivation_method.value if hasattr(f.derivation_method, "value") else f.derivation_method),
            }
            for fid, f in fields_dict.items()
            if f.value is not None
        }

        readiness_dict = {
            "ready_for_stage_14_3": is_complete,
            "is_ready_for_stage_14_2": handoff.readiness.is_ready_for_stage_14_2,
            "reasons": validation_res.blocking_reasons,
            "blocking_reasons": validation_res.blocking_reasons,
        }

        enrichment_pkg = DPREnrichmentPackage(
            metadata={
                "stage": "STAGE_14_2_DPR_ENRICHMENT_INFERENCE",
                "business_id": business_id,
                "scenario_id": active_scenario_id,
                "version": scen_state.version,
                "enriched_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": "14.2.0-FROZEN"
            },
            business_id=business_id,
            scenario_id=active_scenario_id,
            version=scen_state.version,
            intake_package_snapshot=intake_dict,
            business_profile=intake_dict.get("existing_business_profile") or {},
            entrepreneur_profile=intake_dict.get("entrepreneur_context") or {},
            location_profile=intake_dict.get("location_context") or {},
            market=intake_dict.get("market_context") or {},
            market_intelligence=intake_dict.get("market_context") or {},
            opportunity=intake_dict.get("opportunity_context") or {},
            financials=fin_pkg,
            financial_package=fin_pkg,
            benchmarks=benchmark_fields,
            schemes=intake_dict.get("scheme_context") or {},
            scheme_policy_context=intake_dict.get("scheme_context") or {},
            risk=intake_dict.get("risk_context") or {},
            risk_assessment=intake_dict.get("risk_context") or {},
            feasibility=intake_dict.get("feasibility_context") or {},
            feasibility_synthesis=intake_dict.get("feasibility_context") or {},
            swot=intake_dict.get("swot_context") or {},
            swot_matrix=intake_dict.get("swot_context") or {},
            documents=intake_dict.get("documents") or {},
            dpr_fields={fid: f.model_dump() for fid, f in fields_dict.items()},
            modules=mod_summaries,
            sections=sec_summaries,
            section_completeness={sid: s.model_dump() for sid, s in sec_summaries.items()},
            fields=fields_dict,
            gaps=intake_dict.get("gaps") or [],
            assumptions=[a.model_dump() for a in assumption_review.assumptions_requiring_review],
            provenance=prov_dict,
            assumption_review=assumption_review,
            validation=validation_res,
            readiness=readiness_dict,
            is_enrichment_complete=is_complete,
            can_proceed_to_validation=is_complete,
            ready_for_stage_14_3=is_complete
        )

        # HARD CROSS-BUSINESS CONTAMINATION CHECK (Requirement 13)
        if enrichment_pkg.business_id.strip().lower() != business_id.lower():
            raise DPR_STATE_ISOLATION_ERROR(f"requested_business_id={business_id} returned_business_id={enrichment_pkg.business_id}")
        if active_scenario_id and enrichment_pkg.scenario_id.strip().lower() != active_scenario_id.lower():
            raise DPR_STATE_ISOLATION_ERROR(f"requested_scenario_id={active_scenario_id} returned_scenario_id={enrichment_pkg.scenario_id}")

        return self.save_enrichment(enrichment_pkg)

    def _build_assumption_review(
        self,
        business_id: str,
        scenario_id: str,
        version: int,
        fields: Dict[str, EnrichmentField],
        benchmark_fields: Dict[str, Dict[str, Any]],
        user_overrides: Dict[str, Any],
    ) -> AssumptionReviewPackage:
        """
        Creates prioritized review items for domain benchmarks and key drivers.
        """
        review_items: List[AssumptionReviewItem] = []
        info_items: List[AssumptionReviewItem] = []

        # Key assumption fields requiring entrepreneur confirmation
        candidate_fids = [
            "operating_days_per_year",
            "capacity_utilization_year1",
            "working_capital_cycle_days",
            "inventory_holding_period_days",
            "receivables_collection_period_days",
            "creditors_payment_period_days",
            "annual_revenue_growth_rate",
            "gross_profit_margin_pct",
            "operating_shift_structure",
            "power_load_required_hp",
            "water_requirement_daily_liters",
            "moratorium_period_months",
            "loan_tenure_years",
            "interest_rate_term_loan",
        ]

        # Key informational engine outputs to present without requiring confirmation
        informational_fids = [
            "total_project_cost",
            "bank_term_loan_amount",
            "promoter_equity_amount",
            "glance_average_dscr",
            "glance_break_even_utilization",
        ]

        overridden_count = 0
        confirmed_count = 0

        for fid in candidate_fids:
            fld = fields.get(fid)
            if not fld or fld.value is None:
                continue

            is_ovr = fid in user_overrides or fld.is_overridden
            if is_ovr:
                overridden_count += 1
            elif fld.source_type == EnrichmentSourceType.BENCHMARK_DERIVED:
                confirmed_count += 1

            bm_val = fld.baseline_benchmark_value or benchmark_fields.get(fid, {}).get("baseline_benchmark_value")

            review_items.append(
                AssumptionReviewItem(
                    field_id=fid,
                    label=fld.label,
                    module_id=fld.module_id,
                    section_id=fld.section_id,
                    value=fld.value,
                    formatted_value=fld.formatted_value or str(fld.value),
                    unit=fld.unit,
                    source_type=fld.source_type,
                    source_reference=fld.source_reference or "NABARD / MSME Domain Benchmark",
                    confidence=fld.confidence,
                    editable=fld.editable,
                    action=AssumptionReviewAction.USE_OR_CHANGE,
                    why_material=fld.why_material or "Critical operational assumption driving cash flow viability.",
                    baseline_benchmark_value=bm_val,
                    benchmark_id=fld.source_id,
                    is_overridden=is_ovr,
                    downstream_impact=f"Updates downstream schedules in Section {fld.section_id} and banking metrics."
                )
            )

        for fid in informational_fids:
            fld = fields.get(fid)
            if not fld or fld.value is None:
                continue

            info_items.append(
                AssumptionReviewItem(
                    field_id=fid,
                    label=fld.label,
                    module_id=fld.module_id,
                    section_id=fld.section_id,
                    value=fld.value,
                    formatted_value=fld.formatted_value or str(fld.value),
                    unit=fld.unit,
                    source_type=fld.source_type,
                    source_reference=fld.source_reference or "M1-M6 Financial Engine Output",
                    confidence=fld.confidence,
                    editable=False,
                    action=AssumptionReviewAction.INFORMATIONAL,
                    why_material=fld.why_material or "Calculated financial underwriting metric.",
                    downstream_impact="Statutory credit appraisal metric."
                )
            )

        return AssumptionReviewPackage(
            business_id=business_id,
            scenario_id=scenario_id,
            version=version,
            total_assumptions=len(review_items),
            user_confirmed_count=confirmed_count,
            user_overridden_count=overridden_count,
            assumptions_requiring_review=review_items,
            informational_assumptions=info_items
        )

    async def update_assumption(
        self,
        business_id: str,
        field_id: str,
        action: str,  # "OVERRIDE" or "CONFIRM_BENCHMARK"
        value: Optional[Any] = None,
        scenario_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> DPREnrichmentPackage:
        """
        Applies an assumption update (override or benchmark confirmation),
        recalculates M1-M6 engines, updates DPR fields, and refreshes Stage 14.2 package.
        """
        canonical_fid = normalize_field_id(field_id)

        if action == "OVERRIDE":
            dpr_scenario_manager.set_user_override(
                business_id=business_id,
                field_id=canonical_fid,
                value=value,
                scenario_id=scenario_id
            )
        elif action == "CONFIRM_BENCHMARK":
            dpr_scenario_manager.accept_benchmark(
                business_id=business_id,
                field_id=canonical_fid,
                benchmark_value=value,
                scenario_id=scenario_id
            )

        # Trigger authoritative recalculation in Stage 14.1 scenario manager
        await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            changed_field_id=canonical_fid,
            db=db
        )

        # Re-run Stage 14.2 Enrichment
        return await self.run_enrichment(
            business_id=business_id,
            scenario_id=scenario_id,
            db=db
        )


dpr_enrichment_service = DPREnrichmentService()
