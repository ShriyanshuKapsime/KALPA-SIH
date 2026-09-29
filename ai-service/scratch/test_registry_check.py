"""
Script to verify that all 92 DPR fields from ALL_DPR_FIELDS are fully represented in the canonical registry.
"""
import sys
sys.path.insert(0, ".")

from app.services.dpr_stage1.dpr_registry import ALL_DPR_FIELDS, CANONICAL_SECTIONS

print(f"Total fields: {len(ALL_DPR_FIELDS)}")
print(f"Total sections: {len(CANONICAL_SECTIONS)}")

missing_sections = set()
for f in ALL_DPR_FIELDS:
    if f.section_id not in CANONICAL_SECTIONS:
        missing_sections.add(f.section_id)

print(f"Missing sections: {missing_sections}")
