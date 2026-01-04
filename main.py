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
            sd.sleep(500)  # Check every half-second if the stop event is set
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
    recorder = AudioRecorder()

    print("🎤 Recording! (press Enter to stop)", end="")
    recorder.start_recording()
    input()
    recorder.stop_recording()
    print("🎬 Recording stopped.")

    AUDIO_PATH = "/tmp/output.wav"
    recorder.save_recording(AUDIO_PATH)

    client = OpenAI()

    with open(AUDIO_PATH, "rb") as audio_file:
        print("Sending to OpenAI to transcript...")
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file,
            # response_format="text",
        )
        print("-" * 20 + "\n\n" + transcription.text + "\n\n" + "-" * 20)

        print(
            "(Cost: "
            + str(transcription.usage.input_tokens * 6 / 1e6 + transcription.usage.output_tokens * 20 / 1e6)
            + " $)"
        )

        subprocess.run(["xclip", "-sel", "c"], input=transcription.text.encode("utf-8"))
        print("Transcript copied to clipboard.")


if __name__ == "__main__":
    main()
