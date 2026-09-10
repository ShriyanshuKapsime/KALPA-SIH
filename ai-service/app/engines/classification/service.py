"""
Business Classification Engine Interface.
Target: NIC taxonomy matching and rural enterprise ontology mapping (Phase 1).
"""
from app.engines.classification.schemas import ClassificationInput, ClassificationOutput


class BusinessClassificationEngine:
    def __init__(self):
        self.engine_name = "business_classification_engine"

    async def classify(self, input_data: ClassificationInput) -> ClassificationOutput:
        """
        Classify business input into NIC taxonomy. Logic to be implemented during Phase 1.
        """
        return ClassificationOutput(
            nic_2_digit=None,
            nic_5_digit=None,
            industry_title="Unclassified",
            confidence_score=0.0,
            matched_ontology_tags=[]
        )
