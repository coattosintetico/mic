import subprocess
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer


class Language(str, Enum):
    en = "en"
    es = "es"


class AudioRecorder:
    def __init__(self, fs=44100, channels=1):
        self.fs = fs
        self.channels = channels
        self._chunks = []

    def start_recording(self):
        import sounddevice as sd

        self._chunks = []

        def callback(indata, frames, time_info, status):
            self._chunks.append(indata.copy())

        self._stream = sd.InputStream(samplerate=self.fs, channels=self.channels, callback=callback)
        self._stream.start()

    def stop_recording(self):
        # stop() halts the stream; close() releases the device.
        # After stop(), sounddevice guarantees no more callbacks will fire.
        self._stream.stop()
        self._stream.close()

    def get_audio_buffer(self):
        # Only call this after stop_recording() — _chunks must be stable.
        import io

        import numpy as np
        import scipy.io.wavfile as wav

        buf = io.BytesIO()
        recording = np.concatenate(self._chunks, axis=0)
        wav.write(buf, self.fs, recording)
        buf.seek(0)
        buf.name = "audio.wav"  # OpenAI SDK uses .name for MIME-type detection
        return buf


app = typer.Typer()


@app.command()
def main(
    model: Annotated[str, typer.Option(help="Transcription model to use.")] = "gpt-4o-transcribe",
    input_file: Annotated[Optional[Path], typer.Option("-i", "--input", help="Audio file to transcribe instead of recording.")] = None,
    language: Annotated[Optional[Language], typer.Option("-l", "--language", help="Language of the audio (ISO-639-1).")] = None,
):
    # Kick off the openai import in the background while the user is speaking
    # (or while they wait). Python's per-module import lock ensures this is
    # safe: if main reaches `from openai import OpenAI` before this thread
    # finishes, it will simply block until the lock is released.
    def _preload_openai():
        import openai  # side-effect: caches module in sys.modules

    preload_thread = threading.Thread(target=_preload_openai, daemon=True)
    preload_thread.start()

    if input_file is not None:
        audio_buffer = open(input_file, "rb")
    else:
        recorder = AudioRecorder()
        recorder.start_recording()

        print("🎤 Recording! (press Enter to stop)", end="", flush=True)
        input()

        # stop() + close() guarantee the InputStream callback thread is done,
        # so _chunks is fully stable for get_audio_buffer() below.
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

    # Start the spinner before joining preload_thread so the user sees
    # activity even if openai hasn't finished importing yet.
    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()

    preload_thread.join()  # openai is in sys.modules after this
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
                print("\r" + " " * 15 + "\r", end="")  # Clear spinner line
                print("-" * 20)
                print()
                first_chunk = False
            print(event.delta, end="", flush=True)
            full_transcript += event.delta

    print("\n\n" + "-" * 20)

    subprocess.run(["xclip", "-sel", "c"], input=full_transcript.encode("utf-8"))
    print("Transcript copied to clipboard.")


if __name__ == "__main__":
    app()
