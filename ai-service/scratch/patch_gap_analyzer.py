filepath = "ai-service/app/services/dpr_stage1/dpr_gap_analyzer.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# 1. Update imports
old_import = """from app.services.dpr_stage1.dpr_registry import (
    ALL_DPR_FIELDS,
    CANONICAL_MODULES,
    CANONICAL_SECTIONS,
    DPRFieldDefinition,
    FieldMateriality,
    FieldSourceType,
    FieldStatus,
    DPRReadinessStatus,
    get_field_definition,
)"""

new_import = """from app.services.dpr_stage1.dpr_registry import (
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
)"""

if old_import in content:
    content = content.replace(old_import, new_import)
    print("Imports updated in dpr_gap_analyzer.py")
else:
    print("Import replacement note: old_import not matched")

# 2. Update USER_REQUIRED and UNKNOWN gap categorization
old_gap_cat = """            elif status_str in [FieldStatus.USER_REQUIRED.value, "USER_REQUIRED"]:
                user_required_count += 1
                gap_item = self._create_gap_item(field_def, "USER_DECISION", "USER")
                if field_def.materiality == FieldMateriality.CRITICAL or field_def.blocking_if_missing:
                    blocking_gaps.append(gap_item)
                elif field_def.materiality == FieldMateriality.HIGH:
                    high_priority_gaps.append(gap_item)
                else:
                    optional_gaps.append(gap_item)
            elif status_str in [FieldStatus.DOCUMENT_PENDING.value, "DOCUMENT_PENDING"]:
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
                    if field_def.materiality in [FieldMateriality.CRITICAL, FieldMateriality.HIGH] and field_def.blocking_if_missing:
                        blocking_gaps.append(gap_item)
                    elif field_def.materiality in [FieldMateriality.CRITICAL, FieldMateriality.HIGH]:
                        high_priority_gaps.append(gap_item)
                    else:
                        optional_gaps.append(gap_item)"""

new_gap_cat = """            elif status_str in [FieldStatus.USER_REQUIRED.value, "USER_REQUIRED"]:
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
                        optional_gaps.append(gap_item)"""

if old_gap_cat in content:
    content = content.replace(old_gap_cat, new_gap_cat)
    print("Gap categorization patched in dpr_gap_analyzer.py")
else:
    print("ERROR: old_gap_cat not matched")

# 3. Update Readiness Gate logic
old_readiness = """        # Evaluate Stage 14.1 -> Stage 14.2 DPR Intake Readiness Gate
        has_raw_desc = bool(b_intake.get("raw_business_description") or fields.get("business_activity", {}).get("value"))
        has_biz_name = bool(b_intake.get("business_name_as_entered") or fields.get("business_name", {}).get("value"))
        has_promoter = bool(b_intake.get("promoter_name_as_entered") or fields.get("promoter_name", {}).get("value"))
        has_state = bool(b_intake.get("location_state") or fields.get("location_state", {}).get("value"))
        has_district = bool(b_intake.get("location_district") or fields.get("location_district", {}).get("value"))

        # Intake-level blocking gaps are critical basic inputs required for initial profiling
        intake_blocking_fids = {"business_name", "promoter_name", "location_state", "location_district"}
        stage14_blocking_gaps = [
            bg for bg in blocking_gaps 
            if bg.field_id in intake_blocking_fids
        ]

        # Critical conflict check (e.g. user vs verified document or financial imbalance)
        conflicts = dpr_context_package.get("conflicts") or []
        critical_conflicts = [
            c for c in conflicts
            if isinstance(c, dict) and c.get("conflict_type") in ["USER_VS_DOCUMENT", "FINANCIAL_IMBALANCE"]
            and c.get("severity") in ["CRITICAL", "HIGH"]
        ]

        stage_14_2_readiness_reasons: List[str] = []
        if not (has_raw_desc or (has_biz_name and len(str(has_biz_name).strip()) > 2)):
            stage_14_2_readiness_reasons.append("Missing raw business description or commercial activity.")
        if not has_promoter:
            stage_14_2_readiness_reasons.append("Missing promoter / entrepreneur name.")
        if not (has_state and has_district):
            stage_14_2_readiness_reasons.append("Missing target operating location (state and district).")
        if stage14_blocking_gaps:
            stage_14_2_readiness_reasons.append(f"{len(stage14_blocking_gaps)} Stage 14.1 critical intake gaps remain unresolved.")
        if critical_conflicts:
            stage_14_2_readiness_reasons.append(f"{len(critical_conflicts)} critical data conflict(s) require resolution before enrichment.")

        is_ready_for_stage_14_2 = len(stage_14_2_readiness_reasons) == 0
        if is_ready_for_stage_14_2:
            stage_14_2_readiness_reasons.append("Stage 14.1 verified intake package complete. Ready for Stage 14.2 DPR Enrichment & Inference.")

        is_ready_for_stage_2 = is_ready_for_stage_14_2
        stage2_readiness_reasons = list(stage_14_2_readiness_reasons)

        # Evaluate Final DPR Preparation Readiness Gate
        readiness_reasons: List[str] = []
        can_proceed_to_dpr = True
        readiness_status = DPRReadinessStatus.DPR_INPUT_READY

        if blocking_gaps:
            can_proceed_to_dpr = False
            readiness_status = DPRReadinessStatus.DPR_INPUT_INCOMPLETE
            readiness_reasons.append(f"{len(blocking_gaps)} critical inputs required before DPR generation.")
            for bg in blocking_gaps[:3]:
                readiness_reasons.append(f"Missing: {bg.label} ({bg.why_required})")

        fin_pkg = dpr_context_package.get("financial_package") or {}
        if not fin_pkg or not fin_pkg.get("banking_metrics") or not fin_pkg.get("project_cost"):
            t_cost = fields.get("total_project_cost", {}).get("value")
            t_loan = fields.get("bank_term_loan_amount", {}).get("value")
            if not t_cost or not t_loan:
                can_proceed_to_dpr = False
                readiness_status = DPRReadinessStatus.DPR_INPUT_INCOMPLETE
                readiness_reasons.append("Authoritative financial package has not yet calculated project cost and loan.")

        if fin_integrity.get("overall_status") == "FAILED":
            can_proceed_to_dpr = False
            readiness_status = DPRReadinessStatus.DPR_INPUT_INCOMPLETE
            readiness_reasons.extend(fin_integrity.get("reasons", ["Financial integrity checks failed."]))"""

new_readiness = """        # Evaluate Stage 14.1 -> Stage 14.2 DPR Intake Readiness Gate
        bp = dpr_context_package.get("business_profile") or {}
        has_raw_desc = bool(b_intake.get("raw_business_description") or fields.get("business_activity", {}).get("value") or bp.get("business_activity") or bp.get("specific_business") or bp.get("business_name"))
        has_biz_name = bool(b_intake.get("business_name_as_entered") or fields.get("business_name", {}).get("value") or bp.get("business_name") or bp.get("specific_business"))
        has_promoter = bool(b_intake.get("promoter_name_as_entered") or fields.get("promoter_name", {}).get("value") or bp.get("promoter_name") or bp.get("entrepreneur_name"))
        has_state = bool(b_intake.get("location_state") or fields.get("location_state", {}).get("value") or bp.get("location_state") or bp.get("state"))
        has_district = bool(b_intake.get("location_district") or fields.get("location_district", {}).get("value") or bp.get("location_district") or bp.get("district"))

        intake_blocking_fids = {"business_name", "promoter_name", "location_state", "location_district"}
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
            readiness_reasons.extend(fin_integrity.get("reasons", ["Financial integrity checks failed."]))"""

if old_readiness in content:
    content = content.replace(old_readiness, new_readiness)
    print("Readiness gate patched in dpr_gap_analyzer.py")
else:
    print("ERROR: old_readiness not matched")

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESSFULLY APPLIED ALL UPDATES TO dpr_gap_analyzer.py")
