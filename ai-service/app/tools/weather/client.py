"""
Weather and Climate Data Client (IMD, Agro-climatic Zones).
"""
from app.tools.base import BaseTool, ToolResult


class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="weather_tool",
            description="Fetches agro-climatic zone parameters, rainfall averages, and temperature trends."
        )

    async def execute(self, district: str, state: str, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            status="scaffold",
            data={"district": district, "state": state}
        )
