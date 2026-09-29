"""
Safety Net Service (SRP).
-------------------------
Handles fallback responses when all AI models fail.
"""

import asyncio
import time
from collections.abc import AsyncGenerator

from app.core.types import JSONDict
from app.services.llm.degraded_replies import SAFETY_NET_REPLY


class SafetyNetService:
    """
    Provides a static, safe fallback response stream.
    """

    async def stream_safety_response(self) -> AsyncGenerator[JSONDict, None]:
        """Generates the static safety net response."""
        words = SAFETY_NET_REPLY.split(" ")
        for word in words:
            chunk = {
                "id": "safety-net",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "system/safety-net",
                "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}],
            }
            yield chunk  # type: ignore
            await asyncio.sleep(0.05)  # Simulate typing NON-BLOCKING

        # Final chunk
        yield {
            "id": "safety-net",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "system/safety-net",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }  # type: ignore
