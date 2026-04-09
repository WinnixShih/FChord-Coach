import os
import time
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()

_RATE_LIMIT = 2
_call_times: list[float] = []

_SYSTEM_PROMPT = "你是一位吉他老師，專門幫學生矯正 F 和弦指型。"
_USER_TEMPLATE = "學生的手型有問題：{error_type}。給一句簡短（30字以內）、鼓勵的建議。"
_FALLBACK = "慢慢來，專注在目前的問題上，你已經很努力了！"


class VLMService:
    def __init__(self) -> None:
        self._api_key = os.getenv("VLM_API_KEY", "")
        self._provider = os.getenv("VLM_PROVIDER", "anthropic")

    async def suggest(self, error_type: str, landmarks) -> str:
        if not self._can_call():
            return _FALLBACK
        _call_times.append(time.time())
        return await self._call_vlm(error_type)

    def _can_call(self) -> bool:
        now = time.time()
        recent = [t for t in _call_times if now - t < 60]
        _call_times.clear()
        _call_times.extend(recent)
        return len(recent) < _RATE_LIMIT

    async def _call_vlm(self, error_type: str) -> str:
        prompt = _USER_TEMPLATE.format(error_type=error_type)
        if self._provider == "anthropic":
            client = anthropic.AsyncAnthropic(api_key=self._api_key)
            msg = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        client = openai.AsyncOpenAI(api_key=self._api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=100,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content
