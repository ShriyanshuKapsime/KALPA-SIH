"""
KALPA DPR Stage 14.1 → Stage 14.2 Canonical DPR Intake Handoff Contract.
Packages authoritative upstream outputs (Stages 1–13), verified intake, entrepreneur profile,
location, documents, accepted benchmarks, overrides, and readiness state for Stage 14.2 DPR Enrichment.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.services.dpr_stage1.profile_normalizer import profile_normalizer


class RawBusinessInput(BaseModel):
    raw_business_description: Optional[str] = None
    business_name_as_entered: Optional[str] = None
    business_activity_as_described: Optional[str] = None
    products_services_as_described: Optional[str] = None
    target_customer_as_described: Optional[str] = None
    operating_model_as_described: Optional[str] = None
    scale_as_described: Optional[str] = None
    user_language: str = "en"


class BusinessClassificationContext(BaseModel):
    business_node_id: Optional[str] = None
    nic_code: Optional[str] = None
    archetype: Optional[str] = None
    sector: Optional[str] = None
    subcategory: Optional[str] = None
    is_authoritative: bool = True


class EntrepreneurContext(BaseModel):
    promoter_name: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[float] = None
    social_category: Optional[str] = None
    edp_training_status: Optional[str] = None


class LocationContext(BaseModel):
    district: Optional[str] = None
    state: Optional[str] = None
    premises_status: Optional[str] = None
    area_type: Optional[str] = None


class Stage14Readiness(BaseModel):
    is_ready_for_stage_14_2: bool
    status: str
    blocking_gaps_count: int = 0
    unresolved_material_fields: List[str] = Field(default_factory=list)
    pending_documents: List[str] = Field(default_factory=list)
    pending_user_inputs: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

    @property
    def is_ready_for_stage_2(self) -> bool:
        """Backward compatibility alias."""
        return self.is_ready_for_stage_14_2

    @property
    def stage1_status(self) -> str:
        """Backward compatibility alias."""
        return self.status


class DPRStage14HandoffPackage(BaseModel):
    """
    Authoritative Stage 14.1 -> Stage 14.2 Handoff Package Contract (DPR_INTAKE_PACKAGE).
    Transfers complete canonical intake context, upstream stage results, and readiness gates.
    """
    metadata: Dict[str, Any]
    business_identity: Dict[str, Any] = Field(default_factory=dict)
    business_classification: BusinessClassificationContext = Field(default_factory=BusinessClassificationContext)
    raw_user_input: RawBusinessInput
    entrepreneur_context: EntrepreneurContext
    location_context: LocationContext
    business_intent: Dict[str, Any] = Field(default_factory=dict)
    existing_business_profile: Dict[str, Any] = Field(default_factory=dict)
    market_context: Dict[str, Any] = Field(default_factory=dict)
    opportunity_context: Dict[str, Any] = Field(default_factory=dict)
    scheme_context: Dict[str, Any] = Field(default_factory=dict)
    benchmark_context: Dict[str, Any] = Field(default_factory=dict)
    financial_context: Dict[str, Any] = Field(default_factory=dict)
    financial_package: Dict[str, Any] = Field(default_factory=dict)
    risk_context: Dict[str, Any] = Field(default_factory=dict)
    feasibility_context: Dict[str, Any] = Field(default_factory=dict)
    swot_context: Dict[str, Any] = Field(default_factory=dict)
    documents: Dict[str, Any] = Field(default_factory=dict)
    answers: Dict[str, Any] = Field(default_factory=dict)
    accepted_benchmarks: Dict[str, Any] = Field(default_factory=dict)
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    overrides: Dict[str, Any] = Field(default_factory=dict)
    fields: Dict[str, Any] = Field(default_factory=dict)
    unresolved_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    scenario: Dict[str, Any] = Field(default_factory=dict)
    readiness: Stage14Readiness
    stage14_version: str = "14.1.0-FROZEN"


# Backward compatibility aliases
DPRStage1HandoffPackage = DPRStage14HandoffPackage
Stage1HandoffReadiness = Stage14Readiness


def build_stage14_handoff_package(
    dpr_context_package: Optional[Dict[str, Any]] = None,
    gap_analysis_result: Optional[Any] = None,
    *,
    context: Optional[Dict[str, Any]] = None,
    gap_analysis: Optional[Any] = None,
    business_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
) -> DPRStage14HandoffPackage:
    """
    Extracts and validates the canonical Stage 14.1 -> Stage 14.2 handoff structure (DPR_INTAKE_PACKAGE).
    Preserves authoritative upstream classification without downgrade.
    """
    ctx_pkg = dpr_context_package or context or {}
    if hasattr(gap_analysis_result, "model_dump"):
        gap_dict = gap_analysis_result.model_dump()
    elif hasattr(gap_analysis, "model_dump"):
        gap_dict = gap_analysis.model_dump()
    elif isinstance(gap_analysis_result, dict):
        gap_dict = gap_analysis_result
    elif isinstance(gap_analysis, dict):
        gap_dict = gap_analysis
    else:
        gap_dict = {}

    b_intake = ctx_pkg.get("business_intake") or {}
    fields = ctx_pkg.get("fields") or {}
    b_prof = ctx_pkg.get("business_profile") or {}

    raw_input = RawBusinessInput(
        raw_business_description=b_intake.get("raw_business_description") or fields.get("business_activity", {}).get("value"),
        business_name_as_entered=b_intake.get("business_name_as_entered") or fields.get("business_name", {}).get("value"),
        business_activity_as_described=fields.get("business_activity", {}).get("value"),
        products_services_as_described=fields.get("primary_product_name", {}).get("value"),
        target_customer_as_described=fields.get("primary_sales_channel", {}).get("value"),
        operating_model_as_described=fields.get("process_flow_summary", {}).get("value"),
        scale_as_described=str(fields.get("operational_unit_count", {}).get("value") or ""),
        user_language="en"
    )

    raw_edu = fields.get("promoter_education", {}).get("value")
    raw_exp = fields.get("promoter_experience_years", {}).get("value")
    raw_soc = fields.get("promoter_social_category", {}).get("value")
    raw_edp = fields.get("promoter_edp_training_status", {}).get("value")

    norm_edu = profile_normalizer.normalize_education(raw_edu, source_path="fields.promoter_education")
    norm_exp = profile_normalizer.normalize_experience_years(raw_exp, source_path="fields.promoter_experience_years")
    norm_soc = profile_normalizer.normalize_social_category(raw_soc, source_path="fields.promoter_social_category")
    norm_edp = profile_normalizer.normalize_training_status(raw_edp, source_path="fields.promoter_edp_training_status")

    promoter = EntrepreneurContext(
        promoter_name=b_intake.get("promoter_name_as_entered") or fields.get("promoter_name", {}).get("value"),
        education=norm_edu.canonical_value,
        experience_years=norm_exp.canonical_value,
        social_category=norm_soc.canonical_value,
        edp_training_status=norm_edp.canonical_value
    )

    location = LocationContext(
        district=b_intake.get("location_district") or fields.get("location_district", {}).get("value"),
        state=b_intake.get("location_state") or fields.get("location_state", {}).get("value"),
        premises_status=fields.get("premises_status", {}).get("value")
    )

    biz_class = BusinessClassificationContext(
        business_node_id=b_intake.get("business_node_id") or b_prof.get("business_node_id"),
        nic_code=b_intake.get("nic_code") or b_prof.get("nic_code"),
        archetype=b_intake.get("archetype") or b_prof.get("archetype"),
        sector=b_prof.get("sector"),
        subcategory=b_prof.get("subcategory"),
        is_authoritative=bool(b_intake.get("nic_code") or b_prof.get("archetype"))
    )
    blocking_gaps = gap_dict.get("blocking_gaps", [])
    has_essential_intake = bool(
        (raw_input.raw_business_description or raw_input.business_name_as_entered)
        and promoter.promoter_name
        and location.state
        and location.district
    )

    intake_blocking_fids = {"business_name", "promoter_name", "location_state", "location_district"}
    unresolved_intake_gaps = [
        bg for bg in blocking_gaps
        if (isinstance(bg, dict) and bg.get("field_id") in intake_blocking_fids)
        or (hasattr(bg, "field_id") and getattr(bg, "field_id") in intake_blocking_fids)
    ]

    # Stage 14.1 handoff readiness checks intake completeness
    is_ready_from_gap = gap_dict.get("is_ready_for_stage_14_2", gap_dict.get("is_ready_for_stage_2", None))
    if is_ready_from_gap is not None:
        is_ready_stage14_2 = bool(is_ready_from_gap)
    else:
        is_ready_stage14_2 = has_essential_intake and len(unresolved_intake_gaps) == 0

    readiness_reasons: List[str] = list(gap_dict.get("stage_14_2_readiness_reasons") or gap_dict.get("stage2_readiness_reasons") or [])
    if not readiness_reasons:
        if is_ready_stage14_2:
            readiness_reasons.append("Stage 14.1 DPR intake package verified. Ready for Stage 14.2 DPR Enrichment & Deterministic Inference.")
        else:
            if not (raw_input.raw_business_description or raw_input.business_name_as_entered):
                readiness_reasons.append("Missing raw business description or business name.")
            if not promoter.promoter_name:
                readiness_reasons.append("Missing promoter name.")
            if not (location.state and location.district):
                readiness_reasons.append("Missing target location (state and district).")
            if unresolved_intake_gaps:
                readiness_reasons.append(f"{len(unresolved_intake_gaps)} blocking intake gaps require resolution.")

    readiness = Stage14Readiness(
        is_ready_for_stage_14_2=is_ready_stage14_2,
        status="READY_FOR_STAGE_14_2" if is_ready_stage14_2 else "BLOCKED",
        blocking_gaps_count=len(blocking_gaps),
        unresolved_material_fields=[bg.get("field_id") if isinstance(bg, dict) else getattr(bg, "field_id", "") for bg in blocking_gaps],
        pending_documents=[bg.get("field_id") if isinstance(bg, dict) else getattr(bg, "field_id", "") for bg in gap_dict.get("document_pending_gaps", [])],
        pending_user_inputs=[bg.get("field_id") if isinstance(bg, dict) else getattr(bg, "field_id", "") for bg in blocking_gaps if not str(bg).startswith("DOC")],
        reasons=readiness_reasons
    )

    handoff = DPRStage14HandoffPackage(
        metadata={
            "stage": "STAGE_14_1_INTAKE_GAP_RESOLUTION",
            "target_stage": "STAGE_14_2_ENRICHMENT_INFERENCE",
            "business_id": business_id or ctx_pkg.get("business_id"),
            "scenario_id": scenario_id or ctx_pkg.get("scenario_id"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stage14_version": "14.1.0-FROZEN"
        },
        business_identity={
            "business_id": business_id or ctx_pkg.get("business_id"),
            "business_name": raw_input.business_name_as_entered,
            "promoter_name": promoter.promoter_name,
            "raw_business_description": raw_input.raw_business_description,
            "business_activity": raw_input.business_activity_as_described,
            "legal_constitution": fields.get("legal_constitution", {}).get("value"),
        },
        business_classification=biz_class,
        raw_user_input=raw_input,
        entrepreneur_context=promoter,
        location_context=location,
        business_intent={
            "provisional_business_type": b_intake.get("provisional_business_type"),
            "user_business_intent": b_intake.get("user_business_intent")
        },
        existing_business_profile=b_prof,
        market_context=ctx_pkg.get("market_context") or {},
        opportunity_context=ctx_pkg.get("opportunity_context") or {},
        scheme_context=ctx_pkg.get("scheme_context") or {},
        benchmark_context=ctx_pkg.get("assumptions") or {},
        financial_context=ctx_pkg.get("financial_context") or {},
        financial_package=ctx_pkg.get("financial_package") or {},
        risk_context=ctx_pkg.get("risk_context") or {},
        feasibility_context=ctx_pkg.get("feasibility_context") or {},
        swot_context=ctx_pkg.get("swot_context") or {},
        documents=ctx_pkg.get("documents") or {},
        answers=ctx_pkg.get("answers") or {},
        accepted_benchmarks=ctx_pkg.get("accepted_benchmarks") or {},
        assumptions=ctx_pkg.get("assumptions") or {},
        overrides=ctx_pkg.get("overrides") or {},
        fields=fields,
        unresolved_gaps=blocking_gaps,
        conflicts=ctx_pkg.get("conflicts") or [],
        provenance=ctx_pkg.get("provenance") or {},
        scenario={
            "scenario_id": scenario_id or ctx_pkg.get("scenario_id"),
            "last_updated": ctx_pkg.get("last_updated")
        },
        readiness=readiness
    )

    return handoff


# Alias for backward compatibility
build_stage1_handoff_package = build_stage14_handoff_package
build_dpr_intake_package = build_stage14_handoff_package

