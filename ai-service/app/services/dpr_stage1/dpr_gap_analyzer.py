"""
KALPA DPR Stage 1 — Authoritative Gap Analyzer (Hardened / Production Frozen).
Performs deterministic gap discovery across 8 modules and 39 sections.
Categorizes unresolved fields into explicit resolution paths (USER, DOCUMENT, BENCHMARK, STAGE_2, ENGINE, POLICY).
Evaluates real mathematical integrity, provenance completeness, and deterministic readiness gates.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.dpr_stage1.dpr_registry import (
    ALL_DPR_FIELDS,
    CANONICAL_MODULES,
    CANONICAL_SECTIONS,
    DPRFieldDefinition,
    FieldMateriality,
    FieldSourceType,
    FieldStatus,
    DPRReadinessStatus,
    get_field_definition,
)
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    is_question_allowed,
    NEVER_ASKABLE_FIELD_IDS,
)


class GapItem(BaseModel):
    field_id: str
    section_id: str
    module_id: str
    label: str
    gap_category: str
    resolution_path: str  # USER, DOCUMENT, BENCHMARK, STAGE_2, ENGINE, POLICY, DERIVED, UNKNOWN
    materiality: str
    is_blocking: bool
    description: str
    why_required: str
    editable: bool
    downstream_dependencies: List[str] = []
    allowed_values: Optional[List[Any]] = None


class SectionCompletenessSummary(BaseModel):
    section_id: str
    section_number: str
    module_id: str
    title: str
    completeness_status: str
    total_applicable_fields: int
    resolved_fields: int
    unresolved_fields: int
    blocking_gaps_count: int
    document_pending_count: int
    user_required_count: int
    benchmark_populated_count: int
    engine_populated_count: int
    user_populated_count: int


class DPRGapAnalysisResult(BaseModel):
    total_fields: int
    applicable_fields: int
    resolved: int
    benchmark_resolved: int
    engine_resolved: int
    user_resolved: int
    derived: int
    user_required: int
    document_pending: int
    unknown: int
    not_applicable: int
    blocking_gaps: List[GapItem]
    high_priority_gaps: List[GapItem]
    optional_gaps: List[GapItem]
    pending_stage2_gaps: List[GapItem] = Field(default_factory=list)
    document_pending_gaps: List[GapItem] = Field(default_factory=list)
    section_summaries: Dict[str, SectionCompletenessSummary]
    module_summaries: Dict[str, Dict[str, Any]]
    total_sections: int = 39
    completed_sections_count: int = 0
    dpr_readiness_status: DPRReadinessStatus
    can_proceed_to_dpr: bool
    is_ready_for_stage_14_2: bool = True
    is_ready_for_stage_2: bool = True  # Backward compatibility alias
    readiness_reasons: List[str]
    stage_14_2_readiness_reasons: List[str] = Field(default_factory=list)
    stage2_readiness_reasons: List[str] = Field(default_factory=list)
    critical_unresolved_count: int
    financial_integrity_status: str = "UNKNOWN"


class DPRGapAnalyzer:
    """
    Evaluates field-level completeness, resolution paths, and deterministic readiness gates.
    """

    def analyze(self, dpr_context_package: Dict[str, Any]) -> DPRGapAnalysisResult:
        fields = dpr_context_package.get("fields") or {}
        sections = dpr_context_package.get("sections") or {}
        modules = dpr_context_package.get("modules") or {}
        fin_integrity = dpr_context_package.get("financial_integrity") or {}
        b_intake = dpr_context_package.get("business_intake") or {}

        total_fields_count = len(ALL_DPR_FIELDS)
        applicable_count = 0
        resolved_count = 0
        benchmark_resolved_count = 0
        engine_resolved_count = 0
        user_resolved_count = 0
        derived_count = 0
        user_required_count = 0
        doc_pending_count = 0
        unknown_count = 0
        not_applicable_count = 0

        blocking_gaps: List[GapItem] = []
        high_priority_gaps: List[GapItem] = []
        optional_gaps: List[GapItem] = []
        pending_stage2_gaps: List[GapItem] = []
        document_pending_gaps: List[GapItem] = []

        # Audit each registered field
        for field_def in ALL_DPR_FIELDS:
            fid = field_def.field_id
            f_record = fields.get(fid) or {}
            status_str = f_record.get("status") or FieldStatus.UNKNOWN.value
            is_app = f_record.get("applicable", True)

            if not is_app or status_str in [FieldStatus.NOT_APPLICABLE.value, "NOT_APPLICABLE", FieldStatus.PENDING_CLASSIFICATION.value, "PENDING_CLASSIFICATION"]:
                not_applicable_count += 1
                continue

            applicable_count += 1

            if status_str.startswith("RESOLVED_") or status_str in [FieldStatus.BENCHMARK_ACCEPTED.value, "BENCHMARK_ACCEPTED", "DERIVED", "UPSTREAM_RESOLVED", "ENGINE_OUTPUT", "CALCULATED", "DOCUMENT_RESOLVED", "BENCHMARK_RESOLVED", "RESOLVED_DERIVED"]:
                resolved_count += 1
                if status_str in [FieldStatus.RESOLVED_BENCHMARK.value, FieldStatus.BENCHMARK_ACCEPTED.value, "BENCHMARK_ACCEPTED", "BENCHMARK_RESOLVED"]:
                    benchmark_resolved_count += 1
                elif status_str in [FieldStatus.RESOLVED_ENGINE.value, FieldStatus.RESOLVED_POLICY.value, "ENGINE_OUTPUT", "CALCULATED"]:
                    engine_resolved_count += 1
                elif status_str in [FieldStatus.RESOLVED_USER.value, FieldStatus.RESOLVED_OVERRIDE.value, "RESOLVED_OVERRIDE"]:
                    user_resolved_count += 1
                elif status_str in [FieldStatus.RESOLVED_DERIVED.value, "DERIVED"]:
                    derived_count += 1
                else:
                    engine_resolved_count += 1
            elif status_str in [FieldStatus.USER_REQUIRED.value, "USER_REQUIRED"]:
                if is_question_allowed(fid) and fid not in NEVER_ASKABLE_FIELD_IDS and field_def.editable:
                    user_required_count += 1
                    gap_item = self._create_gap_item(field_def, "USER_DECISION", "USER")
                    if field_def.materiality == FieldMateriality.CRITICAL or field_def.blocking_if_missing:
                        blocking_gaps.append(gap_item)
                    elif field_def.materiality == FieldMateriality.HIGH:
                        high_priority_gaps.append(gap_item)
                    else:
                        optional_gaps.append(gap_item)
                else:
                    unknown_count += 1
                    gap_item = self._create_gap_item(field_def, "CALCULATED_OR_DERIVED", "ENGINE")
                    optional_gaps.append(gap_item)
            elif status_str in [FieldStatus.DOCUMENT_PENDING.value, "DOCUMENT_PENDING", "DOCUMENT_REQUIRED"]:
                doc_pending_count += 1
                gap_item = self._create_gap_item(field_def, "DOCUMENT_REQUIRED", "DOCUMENT")
                document_pending_gaps.append(gap_item)
                if field_def.blocking_if_missing:
                    blocking_gaps.append(gap_item)
                else:
                    optional_gaps.append(gap_item)
            else:
                unknown_count += 1
                if fid in ["business_archetype", "nic_code"]:
                    gap_item = self._create_gap_item(field_def, "UPSTREAM_CONTEXT_GAP", "UPSTREAM_CLASSIFIER")
                    pending_stage2_gaps.append(gap_item)
                    optional_gaps.append(gap_item)
                else:
                    res_path = "ENGINE" if not field_def.editable else "UNKNOWN"
                    gap_item = self._create_gap_item(field_def, "TRUE_UNKNOWN", res_path)
                    if field_def.editable and is_question_allowed(fid) and fid not in NEVER_ASKABLE_FIELD_IDS:
                        if field_def.materiality in [FieldMateriality.CRITICAL, FieldMateriality.HIGH] and field_def.blocking_if_missing:
                            blocking_gaps.append(gap_item)
                        elif field_def.materiality in [FieldMateriality.CRITICAL, FieldMateriality.HIGH]:
                            high_priority_gaps.append(gap_item)
                        else:
                            optional_gaps.append(gap_item)
                    else:
                        optional_gaps.append(gap_item)

        # Build Section Summaries
        section_summaries: Dict[str, SectionCompletenessSummary] = {}
        for sid, sdef in CANONICAL_SECTIONS.items():
            sec_record = sections.get(sid) or {}
            sec_fields = sec_record.get("fields") or {}
            app_fields = [f for f in sec_fields.values() if f.get("applicable")]
            res_fields = [f for f in app_fields if str(f.get("status")).startswith("RESOLVED_")]
            user_req = [f for f in app_fields if f.get("status") == FieldStatus.USER_REQUIRED.value]
            doc_pend = [f for f in app_fields if f.get("status") == FieldStatus.DOCUMENT_PENDING.value]
            bench_pop = [f for f in app_fields if f.get("status") == FieldStatus.RESOLVED_BENCHMARK.value]
            eng_pop = [f for f in app_fields if f.get("status") in [FieldStatus.RESOLVED_ENGINE.value, FieldStatus.RESOLVED_POLICY.value]]
            usr_pop = [f for f in app_fields if f.get("status") in [FieldStatus.RESOLVED_USER.value, FieldStatus.RESOLVED_OVERRIDE.value]]
            crit_gaps = [
                f for f in app_fields
                if f.get("status") in [FieldStatus.USER_REQUIRED.value, FieldStatus.DOCUMENT_PENDING.value, FieldStatus.UNKNOWN.value]
                and f.get("materiality") in [FieldMateriality.CRITICAL.value, FieldMateriality.HIGH.value]
                and f.get("blocking_if_missing")
            ]

            status = sec_record.get("completeness_status") or "PARTIALLY_COMPLETE"
            section_summaries[sid] = SectionCompletenessSummary(
                section_id=sid,
                section_number=sdef.section_number,
                module_id=sdef.module_id.value,
                title=sdef.title,
                completeness_status=status,
                total_applicable_fields=len(app_fields),
                resolved_fields=len(res_fields),
                unresolved_fields=len(app_fields) - len(res_fields),
                blocking_gaps_count=len(crit_gaps),
                document_pending_count=len(doc_pend),
                user_required_count=len(user_req),
                benchmark_populated_count=len(bench_pop),
                engine_populated_count=len(eng_pop),
                user_populated_count=len(usr_pop)
            )

        # Build Module Summaries
        module_summaries: Dict[str, Dict[str, Any]] = {}
        for mid, mdef in CANONICAL_MODULES.items():
            sec_ids = mdef.section_ids
            mod_sections = [section_summaries[s] for s in sec_ids if s in section_summaries]
            total_sec = len(mod_sections)
            comp_sec = sum(1 for s in mod_sections if s.completeness_status == "COMPLETE")
            module_summaries[mid.value] = {
                "module_id": mid.value,
                "module_number": mdef.module_number,
                "title": mdef.title,
                "total_sections": total_sec,
                "completed_sections": comp_sec,
                "is_module_ready": comp_sec == total_sec
            }

        # Evaluate Stage 14.1 -> Stage 14.2 DPR Intake Readiness Gate
        bp = dpr_context_package.get("business_profile") or {}
        has_raw_desc = bool(b_intake.get("raw_business_description") or fields.get("business_activity", {}).get("value") or bp.get("business_activity") or bp.get("specific_business") or bp.get("business_name"))
        has_biz_name = bool(b_intake.get("business_name_as_entered") or fields.get("business_name", {}).get("value") or bp.get("business_name") or bp.get("specific_business"))
        has_promoter = bool(b_intake.get("promoter_name_as_entered") or fields.get("promoter_name", {}).get("value") or bp.get("promoter_name") or bp.get("entrepreneur_name"))
        has_state = bool(b_intake.get("location_state") or fields.get("location_state", {}).get("value") or bp.get("location_state") or bp.get("state"))
        has_district = bool(b_intake.get("location_district") or fields.get("location_district", {}).get("value") or bp.get("location_district") or bp.get("district"))

        intake_blocking_fids = {"business_name", "business_activity", "promoter_name", "location_state", "location_district"}
        stage14_blocking_gaps = [
            bg for bg in blocking_gaps 
            if bg.field_id in intake_blocking_fids
        ]

        conflicts = dpr_context_package.get("conflicts") or []
        critical_conflicts = [
            c for c in conflicts
            if isinstance(c, dict) and c.get("conflict_type") in ["USER_VS_DOCUMENT", "FINANCIAL_IMBALANCE"]
            and c.get("severity") in ["CRITICAL", "HIGH"]
        ]

        stage_14_2_readiness_reasons: List[str] = []
        if not (has_raw_desc or (has_biz_name and len(str(has_biz_name).strip()) > 2)):
            stage_14_2_readiness_reasons.append("Missing raw business description or commercial activity.")
        if not has_promoter and "promoter_name" in [bg.field_id for bg in blocking_gaps]:
            stage_14_2_readiness_reasons.append("Missing promoter / entrepreneur name.")
        if not (has_state and has_district) and ({"location_state", "location_district"} & {bg.field_id for bg in blocking_gaps}):
            stage_14_2_readiness_reasons.append("Missing target operating location (state and district).")
        if stage14_blocking_gaps:
            stage_14_2_readiness_reasons.append(f"{len(stage14_blocking_gaps)} Stage 14.1 critical intake gaps remain unresolved.")
        if critical_conflicts:
            stage_14_2_readiness_reasons.append(f"{len(critical_conflicts)} critical data conflict(s) require resolution before enrichment.")

        is_ready_for_stage_14_2 = len(stage_14_2_readiness_reasons) == 0 and len(stage14_blocking_gaps) == 0
        if is_ready_for_stage_14_2:
            stage_14_2_readiness_reasons.append("Stage 14.1 verified intake package complete. Ready for Stage 14.2 DPR Enrichment & Inference.")

        is_ready_for_stage_2 = is_ready_for_stage_14_2
        stage2_readiness_reasons = list(stage_14_2_readiness_reasons)

        # Evaluate Final DPR Preparation Readiness Gate
        readiness_reasons: List[str] = []
        can_proceed_to_dpr = is_ready_for_stage_14_2 and (len(blocking_gaps) == 0)
        readiness_status = DPRReadinessStatus.DPR_INPUT_READY if is_ready_for_stage_14_2 else DPRReadinessStatus.DPR_INPUT_INCOMPLETE

        if blocking_gaps:
            can_proceed_to_dpr = False
            readiness_status = DPRReadinessStatus.DPR_INPUT_INCOMPLETE
            readiness_reasons.append(f"{len(blocking_gaps)} critical inputs required before DPR generation.")
            for bg in blocking_gaps[:3]:
                readiness_reasons.append(f"Missing: {bg.label} ({bg.why_required})")

        fin_pkg = dpr_context_package.get("financial_package") or {}
        if fin_integrity.get("overall_status") == "FAILED":
            can_proceed_to_dpr = False
            readiness_status = DPRReadinessStatus.DPR_INPUT_INCOMPLETE
            readiness_reasons.extend(fin_integrity.get("reasons", ["Financial integrity checks failed."]))

        if can_proceed_to_dpr:
            if high_priority_gaps:
                readiness_status = DPRReadinessStatus.DPR_INPUT_READY
                readiness_reasons.append("Core inputs are ready. Several recommended assumptions can be refined.")
            elif doc_pending_count > 0:
                readiness_status = DPRReadinessStatus.DPR_REVIEW_READY
                readiness_reasons.append("Ready for DPR review. Supporting documents can be attached prior to bank sanction.")
            elif fin_integrity.get("overall_status") == "PASSED":
                readiness_status = DPRReadinessStatus.BANK_REVIEW_READY
                readiness_reasons.append("DPR Context is 100% reconciled and ready for institutional bank credit appraisal.")

        return DPRGapAnalysisResult(
            total_fields=total_fields_count,
            applicable_fields=applicable_count,
            resolved=resolved_count,
            benchmark_resolved=benchmark_resolved_count,
            engine_resolved=engine_resolved_count,
            user_resolved=user_resolved_count,
            derived=derived_count,
            user_required=user_required_count,
            document_pending=doc_pending_count,
            unknown=unknown_count,
            not_applicable=not_applicable_count,
            blocking_gaps=blocking_gaps,
            high_priority_gaps=high_priority_gaps,
            optional_gaps=optional_gaps,
            pending_stage2_gaps=pending_stage2_gaps,
            document_pending_gaps=document_pending_gaps,
            section_summaries=section_summaries,
            module_summaries=module_summaries,
            total_sections=len(section_summaries),
            completed_sections_count=sum(1 for s in section_summaries.values() if s.completeness_status == "COMPLETE"),
            dpr_readiness_status=readiness_status,
            can_proceed_to_dpr=can_proceed_to_dpr,
            is_ready_for_stage_14_2=is_ready_for_stage_14_2,
            is_ready_for_stage_2=is_ready_for_stage_2,
            readiness_reasons=readiness_reasons,
            stage_14_2_readiness_reasons=stage_14_2_readiness_reasons,
            stage2_readiness_reasons=stage2_readiness_reasons,
            critical_unresolved_count=len(blocking_gaps),
            financial_integrity_status=fin_integrity.get("overall_status", "UNKNOWN")
        )

    def _create_gap_item(self, fdef: DPRFieldDefinition, category: str, res_path: str) -> GapItem:
        return GapItem(
            field_id=fdef.field_id,
            section_id=fdef.section_id,
            module_id=fdef.module_id.value,
            label=fdef.label,
            gap_category=category,
            resolution_path=res_path,
            materiality=fdef.materiality.value,
            is_blocking=fdef.blocking_if_missing or fdef.materiality == FieldMateriality.CRITICAL,
            description=fdef.description,
            why_required=fdef.why_required,
            editable=fdef.editable,
            downstream_dependencies=fdef.downstream_dependencies,
            allowed_values=fdef.allowed_values
        )


dpr_gap_analyzer = DPRGapAnalyzer()
