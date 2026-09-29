import sys
sys.path.insert(0, r"c:\Users\shriy\OneDrive\Documents\KALPA SIH\ai-service")
from app.services.dpr_stage1.dpr_canonical_field_registry import CANONICAL_FIELDS, resolve_canonical_id, get_canonical_entry

print("Canonical fields loaded:", len(CANONICAL_FIELDS))
for cid in ["business_archetype", "nic_code", "target_scheme_code", "promoter_experience_years", "covered_area_sqft", "total_project_cost", "dynamic_swot_matrix", "evidence_source_register"]:
    entry = get_canonical_entry(cid)
    print(f"  {cid}: section={entry.section_id}, label={entry.field_label}")
