from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mic.core import transcribe


def _fake_stream(deltas: list[str]):
    for delta in deltas:
        yield SimpleNamespace(type="transcript.text.delta", delta=delta)
    yield SimpleNamespace(type="transcript.text.done")


@patch("openai.OpenAI")
def test_transcribe_concatenates_deltas_and_calls_on_delta(mock_openai_cls) -> None:
    client = MagicMock()
    mock_openai_cls.return_value = client
    client.audio.transcriptions.create.return_value = _fake_stream(["hello", " ", "world"])

    seen: list[str] = []
    result = transcribe(audio=MagicMock(), language="en", prompt="hi", on_delta=seen.append)

    assert result == "hello world"
    assert seen == ["hello", " ", "world"]
    kwargs = client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["language"] == "en"
    assert kwargs["prompt"] == "hi"


@patch("openai.OpenAI")
def test_transcribe_omits_optional_params_when_not_given(mock_openai_cls) -> None:
    client = MagicMock()
    mock_openai_cls.return_value = client
    client.audio.transcriptions.create.return_value = _fake_stream([])

    result = transcribe(audio=MagicMock())

    assert result == ""
    kwargs = client.audio.transcriptions.create.call_args.kwargs
    assert "language" not in kwargs
    assert "prompt" not in kwargs
