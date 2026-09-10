"""
Domain Knowledge Base Interface.
Future content:
- Business categories
- Industry requirements & compliance rules
- Government schemes (PMEGP, Mudra, StandUp India, PMFME)
- Rural enterprise guidelines
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DomainSchemeDoc(BaseModel):
    scheme_id: str
    name: str
    ministry: str
    max_subsidy_percentage: float
    max_project_cost: float
    eligibility_criteria: List[str] = Field(default_factory=list)


class DomainKnowledgeRegistry:
    """
    Registry for static and curated rural industry domain knowledge.
    """
    def __init__(self):
        self.schemes_index: Dict[str, DomainSchemeDoc] = {}

    def get_scheme(self, scheme_id: str) -> Optional[DomainSchemeDoc]:
        return self.schemes_index.get(scheme_id)
