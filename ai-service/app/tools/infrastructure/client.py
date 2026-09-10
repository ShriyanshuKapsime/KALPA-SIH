"""
Infrastructure Data Client (Roads, Power Grids, Water Sources, Cold Storage).
"""
from app.tools.base import BaseTool, ToolResult


class InfrastructureTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="infrastructure_tool",
            description="Evaluates logistics proximity to highways, railheads, 3-phase power, and cold chain hubs."
        )

    async def execute(self, latitude: float, longitude: float, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            status="scaffold",
            data={"lat": latitude, "lon": longitude}
        )
