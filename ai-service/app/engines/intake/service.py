"""
Multilingual Intake Engine Interface.
Target: Phase 1 NLP pipeline, Indic entity extraction, and vernacular transcription.
"""
from app.engines.intake.schemas import RawIntakePayload, ExtractedIntakeProfile


class MultilingualIntakeEngine:
    def __init__(self):
        self.engine_name = "multilingual_intake_engine"

    async def process_intake(self, payload: RawIntakePayload) -> ExtractedIntakeProfile:
        """
        Process speech or text intake. Business logic and Sarvam AI binding to be added in Phase 1.
        """
        return ExtractedIntakeProfile(
            detected_language=payload.language_hint or "hi",
            transcription=payload.raw_content,
            extracted_entities={},
            confidence=0.0
        )
