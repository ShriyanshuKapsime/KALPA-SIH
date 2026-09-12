"""
Retry Policy & Exponential Backoff Engine for Stage 5 Market Intelligence Agent.
Handles transient failures with bounded exponential backoff (1s, 2s, 4s; max 3 attempts).
"""
import asyncio
from typing import Callable, Any, Optional, Dict
from app.core.logging import logger


class NonRetryableError(Exception):
    """Raised when an error is permanent (e.g. invalid arguments, missing mandatory auth)."""
    pass


class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_backoff_sec: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff_sec: float = 8.0
    ):
        self.max_attempts = max_attempts
        self.initial_backoff_sec = initial_backoff_sec
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff_sec = max_backoff_sec

    async def execute_with_retry(
        self,
        coro_fn: Callable[[], Any],
        tool_name: str,
        non_retryable_exceptions: tuple = (NonRetryableError, ValueError, KeyError)
    ) -> Dict[str, Any]:
        """
        Executes an async callable with exponential backoff.
        Returns dict with status, result, attempts_made, and error details if failed.
        """
        attempts = 0
        backoff = self.initial_backoff_sec

        while attempts < self.max_attempts:
            attempts += 1
            try:
                result = await coro_fn()
                return {
                    "success": True,
                    "attempts": attempts,
                    "result": result,
                    "error": None
                }
            except non_retryable_exceptions as e:
                logger.warning(f"[RETRY POLICY] Non-retryable error for tool '{tool_name}': {e}")
                return {
                    "success": False,
                    "attempts": attempts,
                    "result": None,
                    "error": f"Non-retryable: {str(e)}",
                    "non_retryable": True
                }
            except Exception as e:
                logger.warning(f"[RETRY POLICY] Attempt {attempts}/{self.max_attempts} failed for tool '{tool_name}': {e}")
                if attempts >= self.max_attempts:
                    return {
                        "success": False,
                        "attempts": attempts,
                        "result": None,
                        "error": str(e),
                        "non_retryable": False
                    }
                await asyncio.sleep(min(backoff, self.max_backoff_sec))
                backoff *= self.backoff_multiplier


default_retry_policy = RetryPolicy()
