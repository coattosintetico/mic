"""CLI interface for mic."""

import subprocess
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer

from mic.recorder import get_recorder, is_termux

app = typer.Typer(
    name="mic",
    help="Record audio (quickly) from the command line, transcribe it with whisper and copy it to clipboard.",
)


class Language(str, Enum):
    en = "en"
    es = "es"


def _copy_to_clipboard(text: str) -> None:
    if is_termux():
        subprocess.run(["termux-clipboard-set"], input=text.encode("utf-8"))
    else:
        subprocess.run(["xclip", "-sel", "c"], input=text.encode("utf-8"))


@app.command()
def record(
    model: Annotated[str, typer.Option(help="Transcription model to use.")] = "gpt-4o-transcribe",
    input_file: Annotated[
        Optional[Path], typer.Option("-i", "--input", help="Audio file to transcribe instead of recording.")
    ] = None,
    language: Annotated[
        Optional[Language], typer.Option("-l", "--language", help="Language of the audio (ISO-639-1).")
    ] = None,
):
    # Kick off the openai import in the background while the user is speaking.
    def _preload_openai():
        import openai  # noqa: F401  # side-effect: caches module in sys.modules

    preload_thread = threading.Thread(target=_preload_openai, daemon=True)
    preload_thread.start()

    if input_file is not None:
        audio_buffer = open(input_file, "rb")
    else:
        recorder = get_recorder()
        recorder.start_recording()

        print("🎤 Recording! (press Enter to stop)", end="", flush=True)
        input()

        recorder.stop_recording()
        audio_buffer = recorder.get_audio_buffer()

    spinner_chars = r"\|/-"
    spinner_idx = 0
    spinner_stop = threading.Event()

    def spinner():
        nonlocal spinner_idx
        while not spinner_stop.is_set():
            print(f"\rProcessing {spinner_chars[spinner_idx % 4]}", end="", flush=True)
            spinner_idx += 1
            time.sleep(0.1)

    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()

    preload_thread.join()
    from openai import OpenAI

    client = OpenAI()

    stream = client.audio.transcriptions.create(
        model=model,
        file=audio_buffer,
        response_format="text",
        stream=True,
        **({"language": language.value} if language is not None else {}),
    )

    full_transcript = ""
    first_chunk = True
    for event in stream:
        if event.type == "transcript.text.delta":
            if first_chunk:
                spinner_stop.set()
                spinner_thread.join()
                print("\r" + " " * 15 + "\r", end="")
                print("-" * 20)
                print()
                first_chunk = False
            print(event.delta, end="", flush=True)
            full_transcript += event.delta

    print("\n\n" + "-" * 20)

    _copy_to_clipboard(full_transcript)
    print("Transcript copied to clipboard.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
