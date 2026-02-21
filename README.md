# mic

Record and transcribe audio from the terminal using OpenAI Whisper.

## Features

- Records audio until you press Enter
- Transcribes using `gpt-4o-transcribe` model
- Automatically copies the transcript to clipboard
- Shows usage cost per transcription

## Requirements

- Python 3.12+
- Linux with `xclip` installed (for clipboard support)
- OpenAI API key set as `OPENAI_API_KEY` environment variable

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mic.git
cd mic

# Install dependencies with uv
uv sync
```

Or more conveniently:

```bash
uv tool install -e .
```

## Usage

```bash
make run
```

Or directly:

```bash
uv run python main.py
```

The script will:
1. Initialize your microphone
2. Start recording (press Enter to stop)
3. Send the audio to OpenAI for transcription
4. Display the transcript and copy it to your clipboard

## Dependencies

- `openai` — API client for Whisper transcription
- `sounddevice` — microphone access
- `scipy` — WAV file handling

## Development links

- [OpenAI docs for transcription API](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create)
