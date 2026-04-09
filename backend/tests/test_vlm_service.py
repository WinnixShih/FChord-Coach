import time
import pytest
import app.services.vlm_service as vlm_module
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.vlm_service import VLMService


@pytest.fixture(autouse=True)
def clear_rate_limit():
    vlm_module._call_times.clear()
    yield
    vlm_module._call_times.clear()


@pytest.mark.asyncio
async def test_returns_fallback_when_rate_limited() -> None:
    vlm_module._call_times.extend([time.time(), time.time()])
    svc = VLMService()
    result = await svc.suggest("correct", [])
    assert result == "慢慢來，專注在目前的問題上，你已經很努力了！"


@pytest.mark.asyncio
async def test_suggest_delegates_to_call_vlm() -> None:
    svc = VLMService()
    with patch.object(svc, "_call_vlm", new_callable=AsyncMock, return_value="好樣的！") as mock:
        result = await svc.suggest("index_not_barring", [])
    assert result == "好樣的！"
    mock.assert_called_once_with("index_not_barring")


@pytest.mark.asyncio
async def test_call_vlm_anthropic() -> None:
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="食指壓平！")]

    with patch("anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_msg)

        svc = VLMService()
        svc._provider = "anthropic"
        svc._api_key = "test-key"
        result = await svc._call_vlm("index_not_barring")

    assert result == "食指壓平！"
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_call_vlm_openai() -> None:
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="拇指位置調低！"))]

    with patch("openai.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

        svc = VLMService()
        svc._provider = "openai"
        svc._api_key = "test-key"
        result = await svc._call_vlm("thumb_position")

    assert result == "拇指位置調低！"
