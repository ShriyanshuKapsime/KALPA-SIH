"""
Stage 14.2: Evidence & Document Resolver.
Audits document enclosures, extracts statutory facts and vendor quotations,
and resolves field values with verified document provenance.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.dpr_stage2.dpr_enrichment_schemas import (
    EnrichmentField,
    EnrichmentSourceType,
    DerivationMethod,
)

logger = logging.getLogger(__name__)


class EvidenceResolver:
    """
    Extracts deterministic facts from verified enclosure documents.
    """

    DOCUMENT_FIELD_MAPPINGS: Dict[str, List[str]] = {
        "udyam_certificate": ["udyam_registration_number", "business_constitution", "enterprise_category"],
        "pan_card": ["promoter_pan", "enterprise_pan"],
        "aadhaar_card": ["promoter_aadhaar_verified", "promoter_name"],
        "cost_plant_machinery": ["cost_plant_machinery", "vendor_quotation_reference"],
        "premises_lease_agreement": ["premises_status", "monthly_rent_amount"],
        "gst_certificate": ["gstin_number", "gst_applicability"],
        "electricity_bill": ["power_load_sanctioned_hp", "location_operating_address"],
        "fssai_license": ["fssai_registration_number", "food_safety_clearance_status"],
    }

    def resolve_evidence(
        self,
        documents: Dict[str, Any],
        existing_fields: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Processes document evidence registry and produces verified field overlays.
        """
        resolved_evidence: Dict[str, Dict[str, Any]] = {}

        for doc_key, doc_data in documents.items():
            if not isinstance(doc_data, dict):
                continue

            status = doc_data.get("status", "UNKNOWN")
            doc_name = doc_data.get("document_name") or doc_key
            ext_val = doc_data.get("extracted_value")

            # Direct mapping if document key matches a canonical field_id
            if ext_val is not None:
                resolved_evidence[doc_key] = {
                    "value": ext_val,
                    "status": "RESOLVED_DOCUMENT" if status == "VERIFIED" else "DOCUMENT_PROVIDED",
                    "source_type": EnrichmentSourceType.VERIFIED_DOCUMENT if status == "VERIFIED" else EnrichmentSourceType.DOCUMENT_PENDING,
                    "source_id": doc_key,
                    "source_reference": f"Document: {doc_name} (Status: {status})",
                    "confidence": 0.95 if status == "VERIFIED" else 0.70,
                    "derivation_method": DerivationMethod.DOCUMENT_EXTRACTION,
                }

            # Map mapped secondary fields if defined
            secondary_fids = self.DOCUMENT_FIELD_MAPPINGS.get(doc_key, [])
            for sfid in secondary_fids:
                if sfid not in resolved_evidence:
                    if status == "VERIFIED" and ext_val is not None:
                        # Value was extracted directly
                        continue
                    else:
                        resolved_evidence[sfid] = {
                            "value": None,
                            "status": "DOCUMENT_PENDING",
                            "source_type": EnrichmentSourceType.DOCUMENT_PENDING,
                            "source_id": doc_key,
                            "source_reference": f"Enclosure present but value unextracted: {doc_name}",
                            "confidence": 0.50,
                            "derivation_method": DerivationMethod.DOCUMENT_EXTRACTION,
                        }

        return resolved_evidence


evidence_resolver = EvidenceResolver()
