"""
Tool Runner & Asynchronous Execution Engine for Stage 5 Market Intelligence Agent.
Handles dependency resolution, parallel tool execution, cache isolation, and retry orchestration.
"""
import asyncio
import time
from typing import Dict, Any, List, Tuple, Union
from app.schemas.market import MarketExecutionContext
from app.agents.market_intelligence.tools.base_tool import ToolExecutionContext, ToolResult
from app.agents.market_intelligence.tools.tool_registry import market_tool_registry
from app.agents.market_intelligence.execution.caching import market_cache
from app.agents.market_intelligence.execution.retry_policy import default_retry_policy
from app.core.logging import logger


class ToolExecutionEngine:
    """
    Executes selected Stage 5 tools with dependency awareness, concurrency, and cache isolation.
    """

    def __init__(self):
        self.registry = market_tool_registry
        self.cache = market_cache
        self.retry_policy = default_retry_policy

    async def execute_tool_with_caching_and_retry(
        self,
        tool_name: str,
        context: MarketExecutionContext
    ) -> Tuple[str, ToolResult, int, bool]:
        """
        Executes a single tool:
        1. Checks isolated cache
        2. Executes with retry policy if cache miss
        3. Populates cache on success
        Returns (tool_name, tool_result, attempts_count, is_cached)
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            err_result = ToolResult(
                tool_name=tool_name,
                status="failed",
                data_status="FAILED",
                error_message=f"Tool '{tool_name}' is not registered in Stage 5 Tool Registry."
            )
            return tool_name, err_result, 1, False

        # Check Cache with deterministic fingerprint
        cached_data = self.cache.get(tool_name, context)
        if cached_data:
            cached_result = ToolResult(**cached_data)
            cached_result.data_status = "CACHED_VERIFIED_DATA"
            return tool_name, cached_result, 0, True

        # Execute with retry policy
        async def _run():
            return await tool.execute(context)

        exec_res = await self.retry_policy.execute_with_retry(_run, tool_name=tool_name)

        if exec_res["success"]:
            res: ToolResult = exec_res["result"]
            # Cache valid result
            if res.status in ["success", "partial", "unavailable"]:
                self.cache.set(tool_name, context, res.model_dump())
            return tool_name, res, exec_res["attempts"], False
        else:
            err_res = ToolResult(
                tool_name=tool_name,
                status="failed",
                data_status="FAILED",
                error_message=exec_res["error"]
            )
            return tool_name, err_res, exec_res["attempts"], False

    async def run_plan(
        self,
        selected_tools: List[str],
        context: Union[MarketExecutionContext, ToolExecutionContext]
    ) -> Dict[str, Any]:
        """
        Executes a collection plan respecting Stage 5 dependencies and cache isolation.
        Phase 1: Location & Knowledge Hub tools (Foundations)
        Phase 2: Parallel execution of domain, demographic, economic, infrastructure & ML tools.
        """
        start_t = time.perf_counter()

        # Ensure canonical MarketExecutionContext
        if isinstance(context, ToolExecutionContext):
            exec_context = context.to_market_execution_context()
        else:
            exec_context = context

        results: Dict[str, ToolResult] = {}
        tools_called = list(selected_tools)
        successful_tools = []
        failed_tools = []
        retried_tools = []
        cached_tools = []

        # Phase 1: Foundational tools
        foundational = [t for t in selected_tools if t in ["location_intelligence_tool", "knowledge_hub_tool"]]
        for t in foundational:
            name, res, attempts, is_cached = await self.execute_tool_with_caching_and_retry(t, exec_context)
            results[name] = res
            if is_cached:
                cached_tools.append(name)
            if res.status in ["success", "partial", "unavailable"]:
                successful_tools.append(name)
            else:
                failed_tools.append(name)
            if attempts > 1:
                retried_tools.append(name)

        # Phase 2: Domain, demographic, competitor & economic tools in parallel
        remaining = [t for t in selected_tools if t not in foundational]
        if remaining:
            tasks = [self.execute_tool_with_caching_and_retry(t, exec_context) for t in remaining]
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

            for item in parallel_results:
                if isinstance(item, Exception):
                    logger.error(f"[TOOL RUNNER ERROR] Uncaught tool exception: {item}")
                    continue
                name, res, attempts, is_cached = item
                results[name] = res
                if is_cached:
                    cached_tools.append(name)
                if res.status in ["success", "partial", "unavailable"]:
                    successful_tools.append(name)
                else:
                    failed_tools.append(name)
                if attempts > 1:
                    retried_tools.append(name)

        elapsed = time.perf_counter() - start_t

        return {
            "results": results,
            "metadata": {
                "tools_called": tools_called,
                "successful_tools": successful_tools,
                "failed_tools": failed_tools,
                "retried_tools": retried_tools,
                "cached_tools": cached_tools,
                "execution_time_seconds": round(elapsed, 3)
            }
        }


tool_execution_engine = ToolExecutionEngine()
