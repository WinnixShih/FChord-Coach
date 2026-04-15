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
    svc._api_key = "test-key"
    result = await svc.suggest("index_not_barring", [])
    assert result == "慢慢來，專注在目前的問題上，你已經很努力了！"


@pytest.mark.asyncio
async def test_suggest_correct_returns_fixed_message() -> None:
    svc = VLMService()
    svc._api_key = "test-key"
    with patch.object(svc, "_call_vlm", new_callable=AsyncMock) as mock:
        result = await svc.suggest("correct", [])
    assert result == "手型正確，保持這個感覺！"
    mock.assert_not_called()


@pytest.mark.asyncio
async def test_suggest_delegates_to_call_vlm() -> None:
    svc = VLMService()
    svc._api_key = "test-key"
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
async def test_call_vlm_gemini() -> None:
    mock_resp = MagicMock()
    mock_resp.text = "試著把食指壓平！"

    with patch("google.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        svc = VLMService()
        svc._provider = "gemini"
        svc._api_key = "test-key"
        result = await svc._call_vlm("index_not_barring")

    assert result == "試著把食指壓平！"
    mock_client.aio.models.generate_content.assert_called_once()
    config = mock_client.aio.models.generate_content.call_args.kwargs["config"]
    assert config.thinking_config.thinking_budget == 0
    assert config.max_output_tokens == 200


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


class _ApiError(Exception):
    def __init__(self, status_code: int, msg: str = "boom") -> None:
        super().__init__(msg)
        self.status_code = status_code


@pytest.fixture
def no_sleep():
    with patch("app.services.vlm_service.asyncio.sleep", new=AsyncMock()) as m:
        yield m


@pytest.mark.asyncio
async def test_suggest_returns_fallback_when_call_vlm_raises() -> None:
    svc = VLMService()
    svc._api_key = "test-key"
    with patch.object(svc, "_call_vlm", new_callable=AsyncMock, side_effect=_ApiError(503)):
        result = await svc.suggest("index_not_barring", [])
    assert result == "慢慢來，專注在目前的問題上，你已經很努力了！"


@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_error(no_sleep) -> None:
    mock_resp = MagicMock()
    mock_resp.text = "食指壓平！"

    with patch("google.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=[_ApiError(503), mock_resp]
        )
        mock_cls.return_value = mock_client

        svc = VLMService()
        svc._provider = "gemini"
        svc._api_key = "test-key"
        result = await svc._call_vlm("index_not_barring")

    assert result == "食指壓平！"
    assert mock_client.aio.models.generate_content.await_count == 2
    no_sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_exhausts_after_max_attempts(no_sleep) -> None:
    with patch("google.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=_ApiError(503))
        mock_cls.return_value = mock_client

        svc = VLMService()
        svc._provider = "gemini"
        svc._api_key = "test-key"
        with pytest.raises(_ApiError):
            await svc._call_vlm("index_not_barring")

    assert mock_client.aio.models.generate_content.await_count == 3
    assert no_sleep.await_count == 2


@pytest.mark.asyncio
async def test_non_retryable_raises_without_retry(no_sleep) -> None:
    with patch("google.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=_ApiError(400))
        mock_cls.return_value = mock_client

        svc = VLMService()
        svc._provider = "gemini"
        svc._api_key = "test-key"
        with pytest.raises(_ApiError):
            await svc._call_vlm("index_not_barring")

    assert mock_client.aio.models.generate_content.await_count == 1
    no_sleep.assert_not_awaited()
