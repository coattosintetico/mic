# mic

Record audio (quickly) from the command line, transcribe it with whisper and copy it to clipboard.

## Requirements

[uv](https://docs.astral.sh/uv/) — install it with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

Install the CLI globally:

```bash
just install-cli
```

Or without [`just`](https://github.com/casey/just/):

```bash
uv tool install -e .
```

List possible just commands with:

```
just -l
```

## Usage

```bash
mic --help
```

You can also run without installing:

```bash
uv run mic --help
```

or as a module (this runs the CLI):

```bash
uv run python -m mic --help
```

## Termux (Android)

Install system dependencies and grant microphone permission to the Termux:API app in Android settings:

```sh
pkg install python termux-api just uv
```

Set the Android API level (required for building Rust-based dependencies):

```sh
echo 'export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)' >> ~/.bashrc
source ~/.bashrc
```

Then install as usual:

```sh
just install-cli
```

## Development

Set up the development environment:

```bash
just sync-dev
```
