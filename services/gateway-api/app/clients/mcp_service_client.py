from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logger = logging.getLogger(__name__)


class MCPServiceClient:
    """
    Persistent MCP client over Streamable HTTP.

    Production improvements over MVP:
    - startup / shutdown lifecycle
    - one reconnect attempt
    - simple circuit breaker
    - serialized session calls
    - normalized result shape
    """

    def __init__(
        self,
        endpoint_url: str,
        auth_token: Optional[str] = None,
        origin: str = "http://gateway-api.internal",
        timeout_seconds: float = 30.0,
        breaker_threshold: int = 3,
        breaker_cooldown_seconds: int = 20,
        start_retries: int = 6,
        start_retry_delay: float = 2.0,
    ) -> None:
        self.endpoint_url = endpoint_url.rstrip("/")
        self.auth_token = auth_token
        self.origin = origin
        self.timeout_seconds = timeout_seconds
        self.breaker_threshold = breaker_threshold
        self.breaker_cooldown_seconds = breaker_cooldown_seconds
        self.start_retries = start_retries
        self.start_retry_delay = start_retry_delay

        self._http_client: Optional[httpx.AsyncClient] = None
        self._stream_cm = None
        self._session_cm = None
        self._session: Optional[ClientSession] = None

        self._lock = asyncio.Lock()
        self._started = False

        self._consecutive_failures = 0
        self._breaker_opened_until = 0.0
        self._last_success_at: Optional[float] = None

    async def start(self) -> None:
        if self._started:
            return

        last_err: Exception | None = None
        for attempt in range(1, self.start_retries + 1):
            try:
                await self._connect()
                self._started = True
                logger.info("MCP client started for %s", self.endpoint_url)
                return
            except Exception as exc:
                last_err = exc
                await self._cleanup_partial()
                if attempt < self.start_retries:
                    delay = self.start_retry_delay * attempt
                    logger.warning(
                        "MCP connect attempt %d/%d failed for %s: %s — retrying in %.1fs",
                        attempt, self.start_retries, self.endpoint_url, exc, delay,
                    )
                    await asyncio.sleep(delay)

        raise RuntimeError(
            f"Failed to connect to {self.endpoint_url} after {self.start_retries} attempts: {last_err}"
        ) from last_err

    async def _connect(self) -> None:
        headers = {"Origin": self.origin}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds),
            headers=headers,
        )

        self._stream_cm = streamable_http_client(
            self.endpoint_url,
            http_client=self._http_client,
        )
        read_stream, write_stream, _ = await self._stream_cm.__aenter__()

        self._session_cm = ClientSession(read_stream, write_stream)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()

    async def _cleanup_partial(self) -> None:
        """Tear down any partially-opened resources after a failed connect."""
        for cleanup in [
            self._close_session,
            self._close_stream,
            self._close_http,
        ]:
            await cleanup()

    async def _close_session(self) -> None:
        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None
            self._session = None

    async def _close_stream(self) -> None:
        if self._stream_cm is not None:
            try:
                await self._stream_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._stream_cm = None

    async def _close_http(self) -> None:
        if self._http_client is not None:
            try:
                await self._http_client.aclose()
            except Exception:
                pass
            self._http_client = None

    async def stop(self) -> None:
        await self._cleanup_partial()
        self._started = False
        logger.info("MCP client stopped for %s", self.endpoint_url)

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    async def list_tools(self) -> list[str]:
        self._guard_breaker()
        if not self._session:
            raise RuntimeError("MCPServiceClient not started")
        resp = await self._session.list_tools()
        return [t.name for t in resp.tools]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        async with self._lock:
            self._guard_breaker()

            if not self._session:
                raise RuntimeError("MCPServiceClient not started")

            try:
                result = await self._session.call_tool(tool_name, arguments=arguments)
                data = self._normalize_result(result)
                self._mark_success()
                return data

            except Exception as first_error:
                logger.warning("MCP call failed once for tool=%s: %s", tool_name, str(first_error))
                try:
                    await self.restart()
                    if not self._session:
                        raise RuntimeError("MCP reconnect failed")

                    result = await self._session.call_tool(tool_name, arguments=arguments)
                    data = self._normalize_result(result)
                    self._mark_success()
                    return data
                except Exception as second_error:
                    self._mark_failure()
                    raise RuntimeError(f"MCP tool call failed after retry: {second_error}") from second_error

    def _normalize_result(self, result: Any) -> Dict[str, Any]:
        if getattr(result, "isError", False):
            parts: list[str] = []
            for item in getattr(result, "content", []) or []:
                txt = getattr(item, "text", None)
                if txt:
                    parts.append(txt)
            raise RuntimeError(" | ".join(parts) or "MCP tool returned error")

        data = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
        if isinstance(data, dict):
            return data

        text_parts: list[str] = []
        for item in getattr(result, "content", []) or []:
            txt = getattr(item, "text", None)
            if txt:
                text_parts.append(txt)

        raw_text = "\n".join(text_parts).strip()
        if raw_text:
            try:
                maybe = json.loads(raw_text)
                if isinstance(maybe, dict):
                    return maybe
            except Exception:
                pass

        return {
            "answer": raw_text,
            "sources": [],
            "latency_ms": None,
        }

    def _guard_breaker(self) -> None:
        now = time.time()
        if self._breaker_opened_until > now:
            remaining = int(self._breaker_opened_until - now)
            raise RuntimeError(f"MCP circuit breaker open; retry after {remaining}s")

    def _mark_success(self) -> None:
        self._consecutive_failures = 0
        self._breaker_opened_until = 0.0
        self._last_success_at = time.time()

    def _mark_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.breaker_threshold:
            self._breaker_opened_until = time.time() + self.breaker_cooldown_seconds