import os
import json
from typing import List, Dict, Any, Optional
from app.core.logging import logger

PROCESSED_NIC_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "nic", "processed", "official_nic_dataset.json"
)
LEGACY_NIC_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "nic", "nic_codes.json"
)

_NIC_RECORDS: List[Dict[str, Any]] = []
_NIC_INDEX_BY_CODE: Dict[str, Dict[str, Any]] = {}


def load_official_nic_dataset() -> List[Dict[str, Any]]:
    global _NIC_RECORDS, _NIC_INDEX_BY_CODE
    if _NIC_RECORDS:
        return _NIC_RECORDS

    file_to_load = PROCESSED_NIC_FILE if os.path.exists(PROCESSED_NIC_FILE) else LEGACY_NIC_FILE

    try:
        if os.path.exists(file_to_load):
            with open(file_to_load, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                
                # Normalize records into standard hierarchy structure
                _NIC_RECORDS = []
                for item in raw_data:
                    # If already normalized structure
                    if "section" in item and isinstance(item["section"], dict):
                        _NIC_RECORDS.append(item)
                    else:
                        # Convert legacy format to normalized canonical structure
                        div_code = str(item.get("division", "10")).zfill(2)
                        sec_code = "A" if div_code in ["01", "02", "03"] else "G" if div_code in ["45", "46", "47"] else "I" if div_code in ["55", "56"] else "C"
                        rec = {
                            "nic_version": "NIC-2008",
                            "section": {
                                "code": sec_code,
                                "title": "Agriculture" if sec_code == "A" else "Retail & Trade" if sec_code == "G" else "Accommodation & Food" if sec_code == "I" else "Manufacturing"
                            },
                            "division": {
                                "code": div_code,
                                "title": item.get("division_name", item.get("division", ""))
                            },
                            "group": {
                                "code": str(item.get("group", "")),
                                "title": item.get("group_name", item.get("group", ""))
                            },
                            "class": {
                                "code": str(item.get("class", "")),
                                "title": item.get("class_name", item.get("class", ""))
                            },
                            "subclass": {
                                "code": str(item.get("sub_class", item.get("code", ""))),
                                "title": item.get("title", "")
                            },
                            "activity": {
                                "code": str(item.get("code", "")),
                                "title": item.get("title", ""),
                                "description": item.get("description", "")
                            },
                            "keywords": item.get("keywords", []),
                            "source": {
                                "organization": "Government of India / MoSPI",
                                "dataset_version": "NIC-2008 Official Classification Standard",
                                "source_reference": "Central Statistical Office MoSPI"
                            }
                        }
                        _NIC_RECORDS.append(rec)
                        
                _NIC_INDEX_BY_CODE = {r["activity"]["code"]: r for r in _NIC_RECORDS}
                logger.info(f"[NIC REPOSITORY] Loaded {len(_NIC_RECORDS)} official NIC records into memory.")
        else:
            logger.warning(f"[NIC REPOSITORY] NIC dataset file not found at {file_to_load}")
    except Exception as e:
        logger.error(f"[NIC REPOSITORY] Failed loading official NIC dataset: {e}")
        _NIC_RECORDS = []
        _NIC_INDEX_BY_CODE = {}

    return _NIC_RECORDS


def get_official_nic_record(code: str) -> Optional[Dict[str, Any]]:
    load_official_nic_dataset()
    clean_code = str(code).strip()
    return _NIC_INDEX_BY_CODE.get(clean_code)


def search_official_nic_candidates(
    normalized_concept: str,
    keywords: List[str] = None,
    ontology_nic_hints: List[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    records = load_official_nic_dataset()
    if not records:
        return []

    keywords = [k.lower().strip() for k in (keywords or []) if k]
    query = (normalized_concept or "").lower().strip()
    query_tokens = [t for t in query.split() if len(t) > 2]
    
    scored_candidates = []

    for record in records:
        score = 0.0
        code = record["activity"]["code"]
        title = record["activity"]["title"].lower()
        desc = record["activity"]["description"].lower()
        rec_keywords = [k.lower() for k in record.get("keywords", [])]

        # 1. Direct Ontology NIC hint alignment (high weight)
        if ontology_nic_hints and code in ontology_nic_hints:
            score += 0.85

        # 2. Token overlap in title / keywords
        for token in query_tokens:
            if token in rec_keywords:
                score += 0.40
            elif token in title:
                score += 0.35
            elif token in desc:
                score += 0.15

        # 3. Keyword list matches
        for kw in keywords:
            if kw in rec_keywords or kw in title:
                score += 0.30
            elif kw in desc:
                score += 0.15

        # 4. Full concept phrase match
        if query and query in title:
            score += 0.50
        elif query and query in desc:
            score += 0.25

        if score > 0.15:
            cand = dict(record)
            cand["match_score"] = round(min(score, 1.0), 3)
            scored_candidates.append(cand)

    scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_candidates[:limit]
