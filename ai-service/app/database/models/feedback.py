import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import TimeStampedModel


class FeedbackRecord(TimeStampedModel):
    """
    Feedback record for closed-loop learning and agent/model reinforcement.
    """
    __tablename__ = "feedback_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=True)

    feedback_type = Column(String(50), default="intake_accuracy")  # intake_accuracy, feasibility_match, loan_approval
    rating = Column(Integer, nullable=True)  # 1 to 5
    user_comments = Column(Text, nullable=True)
    actual_outcome = Column(String(100), nullable=True)  # e.g., 'loan_sanctioned', 'business_launched'
    meta_attributes = Column(JSON, default=dict)
