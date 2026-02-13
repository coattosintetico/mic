import subprocess
import threading
import time

print("Importing openai module...")
from openai import OpenAI

print("Importing the rest of the modules...")
import scipy.io.wavfile as wav
import sounddevice as sd


class AudioRecorder:
    def __init__(self, fs=44100, channels=1, duration=600):
        self.fs = fs
        self.channels = channels
        self.duration = duration
        self.recording = None
        self.start_time = None
        self.stop_event = threading.Event()

    def record_audio(self):
        self.start_time = time.time()
        self.recording = sd.rec(int(self.duration * self.fs), samplerate=self.fs, channels=self.channels)
        while not self.stop_event.is_set():
            sd.sleep(50)  # Check every 50ms if the stop event is set
        sd.stop()

    def start_recording(self):
        self.thread = threading.Thread(target=self.record_audio)
        self.thread.start()

    def stop_recording(self):
        self.stop_event.set()
        self.thread.join()  # Wait for the recording thread to finish
        end_time = time.time()
        actual_duration = end_time - self.start_time
        self.trim_recording(actual_duration)

    def trim_recording(self, actual_duration):
        # Calculate the number of samples for the actual duration
        num_samples = int(self.fs * actual_duration)
        # Trim the recording to the actual duration
        self.recording = self.recording[:num_samples]

    def save_recording(self, filename):
        wav.write(filename, self.fs, self.recording)  # Save as WAV file


def main():
    print("Initializing microphones...")
    client = OpenAI()
    recorder = AudioRecorder()

    print("🎤 Recording! (press Enter to stop)", end="")
    recorder.start_recording()
    input()
    recorder.stop_recording()

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

    AUDIO_PATH = "/tmp/output.wav"
    recorder.save_recording(AUDIO_PATH)

    with open(AUDIO_PATH, "rb") as audio_file:
        stream = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file,
            response_format="text",
            stream=True,
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
    main()
