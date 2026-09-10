from fastapi import APIRouter, status
from app.schemas.classification import BusinessClassificationRequest, BusinessClassificationResponse

router = APIRouter(prefix="/classification", tags=["Classification"])


@router.post("/classify", response_model=BusinessClassificationResponse, status_code=status.HTTP_200_OK)
async def classify_business(payload: BusinessClassificationRequest):
    """
    Scaffolding endpoint for NIC & ontology classification. Activated during Phase 1.
    """
    return BusinessClassificationResponse(
        primary_category="Unclassified",
        sub_category="General Enterprise",
        confidence_score=0.0,
        matched_nic_codes=[],
        ontology_mappings={}
    )
