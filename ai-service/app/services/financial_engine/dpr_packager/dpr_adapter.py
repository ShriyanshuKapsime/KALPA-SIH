"""
Milestone 6: DPR Ingestion & Normalization Adapter.
Safely extracts M1–M5 outputs from FinancialAnalysisResponse, FinancialAnalysisContainer,
or raw nested dictionaries without mutating or recalculating underlying financial values.
Strictly adheres to UNKNOWN != ZERO: missing values remain None.
"""
from typing import Dict, Any, Optional, Union, List


class DPRIngestionAdapter:
    """
    Normalizes diverse upstream financial objects into clean dictionaries for M6 packaging.
    """

    @staticmethod
    def extract_container(source: Any) -> Dict[str, Any]:
        """
        Unwraps FinancialAnalysisResponse, FinancialAnalysisContainer, or dict.
        """
        if source is None:
            return {}
        
        if hasattr(source, "financial_analysis"):
            fin = getattr(source, "financial_analysis")
            audit = getattr(source, "audit", None)
            res = DPRIngestionAdapter._to_dict(fin)
            res["_analysis_id"] = getattr(source, "analysis_id", None)
            res["_session_id"] = getattr(source, "session_id", None)
            if audit:
                res["_audit"] = DPRIngestionAdapter._to_dict(audit)
            return res
        
        if isinstance(source, dict):
            if "financial_analysis" in source:
                res = dict(source["financial_analysis"])
                res["_analysis_id"] = source.get("analysis_id")
                res["_session_id"] = source.get("session_id")
                if "audit" in source:
                    res["_audit"] = source["audit"]
                return res
            return dict(source)
            
        return DPRIngestionAdapter._to_dict(source)

    @staticmethod
    def _to_dict(obj: Any) -> Dict[str, Any]:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return {}

    @staticmethod
    def safe_get(d: Any, *keys: str, default: Any = None) -> Any:
        """
        Safely retrieves nested value without changing None to default if key exists with None.
        Only returns default if the key is completely missing.
        """
        curr = d
        for k in keys:
            if curr is None:
                return default
            if isinstance(curr, dict):
                if k not in curr:
                    return default
                curr = curr[k]
            elif hasattr(curr, k):
                curr = getattr(curr, k)
            else:
                return default
        return curr


dpr_ingestion_adapter = DPRIngestionAdapter()
