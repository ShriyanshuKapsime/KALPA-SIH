"""
Geospatial Data Client (e.g. OpenStreetMap, Overpass, Bhuvan, Bharat Maps).
"""
from app.tools.base import BaseTool, ToolResult


class GeospatialTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="geospatial_tool",
            description="Queries spatial points of interest, road networks, and market centers."
        )

    async def execute(self, latitude: float, longitude: float, radius_km: float = 5.0, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            status="scaffold",
            data={"lat": latitude, "lon": longitude, "radius": radius_km}
        )
