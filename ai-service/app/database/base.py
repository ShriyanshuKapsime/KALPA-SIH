import datetime
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import Column, DateTime, Integer


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models with standard audit timestamps.
    """
    pass


class TimeStampedModel(Base):
    """
    Abstract base model providing created_at and updated_at timestamps.
    """
    __abstract__ = True

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )
