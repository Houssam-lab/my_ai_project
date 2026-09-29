"""
Dummy Safety Net Service.
"""

from collections.abc import AsyncGenerator

from microservices.orchestrator_service.src.core.degraded_replies import SERVER_PRESSURE_REPLY


class SafetyNetService:
    async def stream_safety_response(self) -> AsyncGenerator[dict[str, object], None]:
        yield {"choices": [{"delta": {"content": SERVER_PRESSURE_REPLY}}]}
