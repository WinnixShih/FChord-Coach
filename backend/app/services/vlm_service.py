import os
import time
import anthropic
import openai
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_RATE_LIMIT = 2
_call_times: list[float] = []

_ERROR_LABELS: dict[str, str] = {
    "correct": "手型正確",
    "index_not_barring": "食指未橫壓",
    "thumb_position": "拇指位置不對",
    "ring_pinky_curl": "無名指／小指未彎曲",
    "wrist_angle": "手腕角度不對",
}

_CORRECT_MESSAGE = "手型正確，保持這個感覺！"

_SYSTEM_PROMPT = (
    "你是一位專業吉他老師，專門幫學生矯正 F 和弦指型。"
    "語氣溫和但具體，必須明確指出要修正的動作，而不是空泛地鼓勵。"
    "輸出規則：只輸出一句繁體中文，最多 30 字；"
    "不得使用 Markdown、星號、項目符號、emoji、換行或任何格式符號；"
    "不得稱讚錯誤姿勢；不得使用簡體字。"
)

_USER_TEMPLATE = (
    "學生目前的 F 和弦問題是：{error_label}。"
    "請用一句話（≤30 字）告訴他具體該怎麼調整手型來修正這個問題。"
)

_FALLBACK = "慢慢來，專注在目前的問題上，你已經很努力了！"


class VLMService:
    def __init__(self) -> None:
        self._api_key = os.getenv("VLM_API_KEY", "")
        self._provider = os.getenv("VLM_PROVIDER", "gemini")

    async def suggest(self, error_type: str, landmarks) -> str:
        if error_type == "correct":
            return _CORRECT_MESSAGE
        if not self._api_key or not self._can_call():
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
        error_label = _ERROR_LABELS.get(error_type, error_type)
        prompt = _USER_TEMPLATE.format(error_label=error_label)
        if self._provider == "gemini":
            client = genai.Client(api_key=self._api_key)
            resp = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    max_output_tokens=200,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            return resp.text
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
