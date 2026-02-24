"""Audio recorders."""

import os
import platform
import subprocess
import tempfile


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
        fd, self._tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    def start_recording(self):
        self._proc = subprocess.Popen(
            ["ffmpeg", "-y", *_ffmpeg_input_args(), self._tmp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop_recording(self):
        self._proc.stdin.write(b"q")
        self._proc.stdin.flush()
        self._proc.wait()

    def get_audio_buffer(self):
        return open(self._tmp_path, "rb")


class TermuxRecorder:
    """Records audio via termux-microphone-record.

    termux-microphone-record starts recording in the background and returns
    immediately; -e stops it and flushes the file.
    """

    def __init__(self):
        fd, self._tmp_path = tempfile.mkstemp(suffix=".m4a")
        os.close(fd)
        os.unlink(self._tmp_path)

    def start_recording(self):
        subprocess.run(["termux-microphone-record", "-f", self._tmp_path], check=True, stdout=subprocess.DEVNULL)

    def stop_recording(self):
        subprocess.run(["termux-microphone-record", "-q"], check=True, stdout=subprocess.DEVNULL)

    def get_audio_buffer(self):
        return open(self._tmp_path, "rb")


def get_recorder():
    return TermuxRecorder() if is_termux() else FfmpegRecorder()
