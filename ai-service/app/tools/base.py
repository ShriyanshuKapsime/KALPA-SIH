"""
Base Tool Interface for Agent Tool Layer.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    tool_name: str
    status: str = "success"  # success, error, disabled
    data: Dict[str, Any] = {}
    error_message: Optional[str] = None


class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool query against an external data source or API.
        """
        raise NotImplementedError("Tool execution will be implemented in subsequent phases.")
