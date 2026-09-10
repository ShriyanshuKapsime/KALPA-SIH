from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Standard Health Check Response.
    """
    status: str = Field(default="healthy", description="Service health state")
    service: str = Field(default="kalpa-ai-service", description="Service identifier")
    version: str = Field(default="0.1.0", description="Service version")
    environment: str = Field(default="development", description="Runtime environment")
    database_connected: bool = Field(default=False, description="Status of DB connectivity")
    spatial_enabled: bool = Field(default=True, description="PostGIS readiness")
    vector_enabled: bool = Field(default=True, description="pgvector readiness")


class SystemInfoResponse(BaseModel):
    project_name: str
    tagline: str
    components: Dict[str, str]
