SHELL := /bin/bash
.SHELLFLAGS := -eo pipefail -c
.DEFAULT_GOAL := help

MODEL := mlx-community/whisper-large-v3-turbo

.PHONY: help init start

help:
	@echo "make init    one-time setup: ffmpeg, uv, Python env, Whisper model (~1.6 GB)"
	@echo "make start   asks for a video, saves transcript to your Desktop"

init:
	@[ "$$(uname -s)" = "Darwin" ] && [ "$$(uname -m)" = "arm64" ] || { echo "ERROR: Mac with Apple Silicon (M1 or newer) required"; exit 1; }
	@command -v brew >/dev/null || { echo "ERROR: install Homebrew first: https://brew.sh"; exit 1; }
	@command -v ffmpeg >/dev/null || brew install ffmpeg
	@command -v uv >/dev/null || brew install uv
	uv sync --locked
	uv run python -c "from huggingface_hub import snapshot_download as d; d('$(MODEL)')"
	@uv run python -c "import mlx_whisper; print('OK: ready. Now run: make start')"

start:
	@caffeinate -ims uv run --locked python -u transcribe.py
