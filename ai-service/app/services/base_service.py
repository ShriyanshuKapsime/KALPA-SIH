"""
Base Service Class for Application Logic Layer.
"""
from typing import Optional
from sqlalchemy.orm import Session


class BaseService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
