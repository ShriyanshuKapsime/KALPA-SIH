"""
Stage 14.2: Deterministic Inference Engine.
Consumes authoritative M1–M6 financial packages and upstream Stage 1–13 intelligence,
applies deterministic inference rules, and populates all 8 modules and 39 canonical DPR sections without LLM hallucination.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.dpr_stage1.dpr_registry import (
    ALL_DPR_FIELDS,
    CANONICAL_MODULES,
    CANONICAL_SECTIONS,
    DPRFieldDefinition,
    FieldMateriality,
    FieldSourceType,
    get_field_definition,
    normalize_field_id,
)
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    resolve_field_semantically,
    FieldResolutionStatus,
    CANONICAL_FIELDS,
)
from app.services.dpr_stage2.dpr_enrichment_schemas import (
    EnrichmentField,
    EnrichmentSourceType,
    DerivationMethod,
    SectionEnrichmentSummary,
    ModuleEnrichmentSummary,
    AUTHORITATIVE_FINANCIAL_FIELDS,
)

logger = logging.getLogger(__name__)


def _normalize_confidence(c: Any) -> float:
    """Safely converts confidence to a standard float between 0.0 and 1.0."""
    if isinstance(c, (int, float)):
        return float(c)
    if isinstance(c, str):
        c_upper = c.strip().upper()
        mapping = {
            "CONFIRMED": 1.0,
            "HIGH": 0.9,
            "MEDIUM": 0.7,
            "ESTIMATED": 0.6,
            "LOW": 0.4,
            "PROVISIONAL": 0.5,
            "UNKNOWN": 0.0,
        }
        if c_upper in mapping:
            return mapping[c_upper]
        try:
            return float(c)
        except ValueError:
            return 0.5
    return 0.0


def safe_num(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class DeterministicInferenceEngine:
    """
    Synthesizes multi-source inputs into an enriched 39-section DPR context.
    Consumes authoritative M1-M6 financial outputs and strictly preserves source provenance.
    """

    def infer_dpr_context(
        self,
        business_id: str,
        scenario_id: str,
        intake_package: Dict[str, Any],
        evidence_fields: Dict[str, Dict[str, Any]],
        benchmark_fields: Dict[str, Dict[str, Any]],
        market_fields: Dict[str, Dict[str, Any]],
        policy_fields: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Executes end-to-end deterministic inference consuming authoritative M1-M6 financial packages.
        """
        user_answers = intake_package.get("answers") or intake_package.get("user_answers") or {}
        user_overrides = intake_package.get("overrides") or intake_package.get("user_overrides") or {}
        prev_fields = intake_package.get("fields") or {}
        fin_package = intake_package.get("financial_package") or {}
        b_class = intake_package.get("business_classification") or {}
        cat_str = b_class.get("archetype") or intake_package.get("business_profile", {}).get("archetype")
        nic_str = b_class.get("nic_code") or intake_package.get("business_profile", {}).get("nic_code")

        bp_data = (
            intake_package.get("business_profile")
            or intake_package.get("existing_business_profile")
            or intake_package.get("business_identity")
            or {}
        )
        if isinstance(bp_data, dict):
            bp_data = dict(bp_data)
            if not bp_data.get("business_id"):
                bp_data["business_id"] = business_id
            if not bp_data.get("scenario_id"):
                bp_data["scenario_id"] = scenario_id

        sources = {
            "business_id": business_id,
            "scenario_id": scenario_id,
            "user_overrides": user_overrides,
            "user_answers": user_answers,
            "documents": intake_package.get("documents") or {},
            "financial_package": fin_package,
            "business_profile": bp_data,
            "entrepreneur_profile": intake_package.get("entrepreneur_context") or intake_package.get("entrepreneur_profile") or {},
            "entrepreneur_readiness": intake_package.get("entrepreneur_readiness") or {},
            "location_profile": intake_package.get("location_context") or intake_package.get("location_profile") or {},
            "market_context": intake_package.get("market_context") or {},
            "opportunity_context": intake_package.get("opportunity_context") or {},
            "risk_context": intake_package.get("risk_context") or {},
            "swot_context": intake_package.get("swot_context") or {},
            "feasibility_context": intake_package.get("feasibility_context") or {},
            "benchmarks": benchmark_fields or intake_package.get("benchmarks") or {},
            "policy_data": policy_fields or intake_package.get("policy_data") or {},
            "classification": b_class,
            "raw_intake": intake_package.get("raw_intake") or intake_package.get("raw_user_input") or {},
            "previous_fields": prev_fields,
        }

        # Resolve Every Registered Canonical Field across 9 Modules / 39 Sections
        enriched_fields: Dict[str, EnrichmentField] = {}

        for fdef in ALL_DPR_FIELDS:
            fid = fdef.field_id
            c_fid = normalize_field_id(fid)

            sem_res = resolve_field_semantically(field_id=fid, sources=sources, archetype=cat_str)
            val = sem_res.get("value")
            status = sem_res.get("status", "UNKNOWN")
            source_id = sem_res.get("source_module") or sem_res.get("source_path") or "CANONICAL_RESOLVER"
            source_ref = sem_res.get("source_path") or f"Resolved via {sem_res.get('resolution_method')}"
            conf = sem_res.get("confidence", 1.0 if val is not None else 0.0)

            # Map status to EnrichmentSourceType
            if status == "RESOLVED_USER":
                source_type = EnrichmentSourceType.USER_PROVIDED
                derivation = DerivationMethod.DIRECT_INPUT
            elif status == "RESOLVED_OVERRIDE":
                source_type = EnrichmentSourceType.USER_OVERRIDE
                derivation = DerivationMethod.DIRECT_INPUT
            elif status == "RESOLVED_ENGINE":
                source_type = EnrichmentSourceType.ENGINE_CALCULATED
                derivation = DerivationMethod.FINANCIAL_ENGINE_M1_M6
            elif status == "RESOLVED_DOCUMENT":
                source_type = EnrichmentSourceType.VERIFIED_DOCUMENT
                derivation = DerivationMethod.DOCUMENT_EXTRACTION
            elif status == "RESOLVED_MARKET":
                source_type = EnrichmentSourceType.MARKET_DERIVED
                derivation = DerivationMethod.MARKET_SIGNAL
            elif status == "RESOLVED_POLICY":
                source_type = EnrichmentSourceType.POLICY_DERIVED
                derivation = DerivationMethod.STATUTORY_POLICY
            elif status == "RESOLVED_BENCHMARK":
                source_type = EnrichmentSourceType.BENCHMARK_DERIVED
                derivation = DerivationMethod.INDUSTRY_BENCHMARK
            elif status == "DERIVED":
                source_type = EnrichmentSourceType.DERIVED
                derivation = DerivationMethod.FORMULAIC_CALCULATION
            elif status == "RESOLVED_UPSTREAM":
                source_type = EnrichmentSourceType.UPSTREAM_RESOLVED
                derivation = DerivationMethod.DIRECT_INPUT
            elif status == "NOT_APPLICABLE":
                source_type = EnrichmentSourceType.NOT_APPLICABLE
                derivation = DerivationMethod.UNRESOLVED
            elif status == "SOURCE_MAPPING_ERROR":
                source_type = EnrichmentSourceType.SOURCE_MAPPING_ERROR
                derivation = DerivationMethod.UNRESOLVED
            else:
                source_type = EnrichmentSourceType.UNKNOWN
                derivation = DerivationMethod.UNRESOLVED

            is_overridden = bool(c_fid in user_overrides or fid in user_overrides)
            baseline_val = benchmark_fields.get(c_fid, {}).get("baseline_benchmark_value") if isinstance(benchmark_fields, dict) else None

            # Format Value
            fmt_val = None
            if val is not None:
                if isinstance(val, (int, float)):
                    if fdef.field_type == "currency":
                        fmt_val = f"₹{val:,.0f}"
                    elif fdef.unit == "%":
                        fmt_val = f"{val:.1f}%"
                    elif fdef.unit == "x":
                        fmt_val = f"{val:.2f}x"
                    else:
                        fmt_val = f"{val:,.0f} {fdef.unit}".strip() if fdef.unit else f"{val:,.0f}"
                elif isinstance(val, list):
                    fmt_val = f"{len(val)} items populated"
                elif isinstance(val, dict):
                    fmt_val = "Structured Data"
                else:
                    fmt_val = str(val)

            if status == "NOT_APPLICABLE":
                final_status = "NOT_APPLICABLE"
                final_source_type = EnrichmentSourceType.NOT_APPLICABLE
            elif val is not None:
                final_status = status
                final_source_type = source_type
            else:
                final_status = "USER_REQUIRED" if fdef.editable and fdef.materiality == FieldMateriality.CRITICAL else "UNKNOWN"
                final_source_type = EnrichmentSourceType.UNKNOWN

            enriched_fields[fid] = EnrichmentField(
                field_id=fid,
                section_id=fdef.section_id,
                module_id=fdef.module_id.value,
                label=fdef.label,
                value=val,
                formatted_value=fmt_val,
                unit=fdef.unit,
                status=final_status,
                source_type=final_source_type,
                source_id=source_id,
                source_reference=source_ref or ("Pending input" if val is None else "KALPA System"),
                confidence=_normalize_confidence(conf),
                derivation_method=derivation,
                upstream_dependencies=fdef.downstream_dependencies,
                editable=fdef.editable,
                materiality=fdef.materiality.value,
                why_material=fdef.why_required,
                baseline_benchmark_value=baseline_val,
                is_overridden=is_overridden
            )

        # Build Section Summaries & Module Summaries across all Canonical Sections and Modules
        section_summaries: Dict[str, SectionEnrichmentSummary] = {}
        for sid, sdef in CANONICAL_SECTIONS.items():
            sec_fields = {fid: fld for fid, fld in enriched_fields.items() if fld.section_id == sid}
            res_fields = [f for f in sec_fields.values() if f.value is not None]
            unres_fields = [f for f in sec_fields.values() if f.value is None]

            source_counts: Dict[str, int] = {}
            for rf in res_fields:
                st_str = rf.source_type.value
                source_counts[st_str] = source_counts.get(st_str, 0) + 1

            comp_status = "COMPLETE" if len(unres_fields) == 0 else ("PARTIALLY_COMPLETE" if len(res_fields) > 0 else "INCOMPLETE")

            section_summaries[sid] = SectionEnrichmentSummary(
                section_id=sid,
                section_number=sdef.section_number,
                module_id=sdef.module_id.value,
                title=sdef.title,
                total_fields=len(sec_fields),
                resolved_fields=len(res_fields),
                unresolved_fields=len(unres_fields),
                completeness_status=comp_status,
                source_breakdown=source_counts,
                fields=sec_fields
            )

        module_summaries: Dict[str, ModuleEnrichmentSummary] = {}
        for mid, mdef in CANONICAL_MODULES.items():
            sec_ids = mdef.section_ids
            mod_secs = {s: section_summaries[s] for s in sec_ids if s in section_summaries}
            tot_f = sum(s.total_fields for s in mod_secs.values())
            res_f = sum(s.resolved_fields for s in mod_secs.values())
            comp_s = sum(1 for s in mod_secs.values() if s.completeness_status == "COMPLETE")

            module_summaries[mid.value] = ModuleEnrichmentSummary(
                module_id=mid.value,
                module_number=mdef.module_number,
                title=mdef.title,
                description=mdef.description,
                total_sections=len(mod_secs),
                completed_sections=comp_s,
                total_fields=tot_f,
                resolved_fields=res_f,
                is_module_ready=comp_s == len(mod_secs),
                sections=mod_secs
            )

        return {
            "fields": enriched_fields,
            "sections": section_summaries,
            "modules": module_summaries,
            "financial_package": fin_package
        }


deterministic_inference_engine = DeterministicInferenceEngine()
