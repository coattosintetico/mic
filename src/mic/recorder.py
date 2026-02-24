"""Audio recorders."""

import datetime
import os
import platform
import subprocess
import time
from pathlib import Path

RECORDINGS_DIR = Path("/tmp/mic")


def _recording_path(ext: str) -> Path:
    RECORDINGS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return RECORDINGS_DIR / f"{ts}.{ext}"


def is_termux() -> bool:
    return "TERMUX_VERSION" in os.environ


def _ffmpeg_input_args() -> list[str]:
    """Platform-specific ffmpeg input format flags."""
    system = platform.system()
    if system == "Linux":
        return ["-f", "pulse", "-i", "default"]
    elif system == "Darwin":
        return ["-f", "avfoundation", "-i", ":0"]
    else:
        raise RuntimeError(f"Unsupported platform for ffmpeg recording: {system}")


class FfmpegRecorder:
    def __init__(self):
        self._path = _recording_path("wav")

    def start_recording(self):
        self._proc = subprocess.Popen(
            ["ffmpeg", "-y", *_ffmpeg_input_args(), str(self._path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop_recording(self):
        self._proc.stdin.write(b"q")
        self._proc.stdin.flush()
        self._proc.wait()

    def get_audio_buffer(self):
        return open(self._path, "rb")


class TermuxRecorder:
    """Records audio via termux-microphone-record.

    termux-microphone-record starts recording in the background and returns
    immediately; -e stops it and flushes the file.
    """

    def __init__(self):
        self._path = _recording_path("m4a")

    def start_recording(self):
        subprocess.run(["termux-microphone-record", "-f", str(self._path)], check=True, stdout=subprocess.DEVNULL)

    def stop_recording(self):
        subprocess.run(["termux-microphone-record", "-q"], check=True, stdout=subprocess.DEVNULL)

    def get_audio_buffer(self):
        deadline = time.monotonic() + 10
        while not self._path.exists():
            if time.monotonic() > deadline:
                raise RuntimeError(f"Recording file never appeared: {self._path}")
            time.sleep(0.1)
        return open(self._path, "rb")


def get_recorder():
    return TermuxRecorder() if is_termux() else FfmpegRecorder()
