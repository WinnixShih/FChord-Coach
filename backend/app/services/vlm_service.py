import os
import time
from dotenv import load_dotenv

load_dotenv()

_RATE_LIMIT = 2  # max calls per minute
_call_times: list[float] = []


class VLMService:
    def __init__(self):
        self._api_key = os.getenv("VLM_API_KEY", "")
        self._provider = os.getenv("VLM_PROVIDER", "openai")  # openai | anthropic

    async def suggest(self, error_type: str, landmarks) -> str:
        if not self._can_call():
            return "Practice slowly and focus on the identified issue."
        _call_times.append(time.time())
        return await self._call_vlm(error_type)

    def _can_call(self) -> bool:
        now = time.time()
        recent = [t for t in _call_times if now - t < 60]
        _call_times.clear()
        _call_times.extend(recent)
        return len(recent) < _RATE_LIMIT

    async def _call_vlm(self, error_type: str) -> str:
        # TODO: integrate GPT-4o or Claude based on VLM_PROVIDER
        prompt = f"The player's F chord has an error: {error_type}. Give a short, encouraging tip."
        return f"[VLM] Tip for {error_type}: focus on your finger placement."
