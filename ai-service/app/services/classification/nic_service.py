"""
NIC Service wrapper forwarding to official NIC repository.
Maintains backward compatibility with legacy endpoints and tests.
"""

from typing import List, Dict, Any, Optional
from app.services.classification.nic_repository import (
    load_official_nic_dataset,
    get_official_nic_record,
    search_official_nic_candidates
)


def load_nic_data() -> List[Dict[str, Any]]:
    return load_official_nic_dataset()


def get_nic_by_code(code: str) -> Optional[Dict[str, Any]]:
    return get_official_nic_record(code)


def search_nic_candidates(
    normalized_concept: str,
    keywords: List[str] = None,
    ontology_nic_hints: List[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    return search_official_nic_candidates(
        normalized_concept=normalized_concept,
        keywords=keywords,
        ontology_nic_hints=ontology_nic_hints,
        limit=limit
    )
