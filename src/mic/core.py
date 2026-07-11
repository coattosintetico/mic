"""Core logic for mic."""

from typing import BinaryIO, Callable, Optional


def transcribe(
    audio: BinaryIO,
    model: str = "gpt-4o-transcribe",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    on_delta: Optional[Callable[[str], None]] = None,
) -> str:
    """Transcribe an audio buffer with OpenAI.

    The transcription is streamed; `on_delta` (if given) is called with each text
    chunk as it arrives. Returns the full transcript.
    """
    from openai import OpenAI

    client = OpenAI()
    stream = client.audio.transcriptions.create(
        model=model,
        file=audio,
        response_format="text",
        stream=True,
        **({"language": language} if language is not None else {}),
        **({"prompt": prompt} if prompt is not None else {}),
    )

    full_transcript = ""
    for event in stream:
        if event.type == "transcript.text.delta":
            if on_delta is not None:
                on_delta(event.delta)
            full_transcript += event.delta
    return full_transcript
