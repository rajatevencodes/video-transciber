# video-transcriber

Turn a local video into a timestamped English transcript on your Desktop. Runs fully offline with OpenAI Whisper (large-v3-turbo) on the Apple Silicon GPU via `mlx-whisper`.

## Requirements

* Mac with Apple Silicon (M1 or newer)
* [Homebrew](https://brew.sh)
* `make` (run `xcode-select --install` if missing)

## Setup (one time)

```bash
git clone <this-repo-url>
cd video-transcriber
make init
```

`make init` installs ffmpeg and uv if missing, creates the Python env with uv, and downloads the Whisper model (~1.6 GB).

## Use

```bash
make start
```

Drag the video file into the terminal (or paste its path) and press Enter.

Output: `~/Desktop/<video_name>_transcript.txt`. Same name is overwritten.

```
SOURCE: lecture01.mp4
DURATION: 01:58:12
LANGUAGE: English
MODEL: mlx-community/whisper-large-v3-turbo
SEGMENTS: 2140
FORMAT: one line per segment, [HH:MM:SS] = start time in the video
---
[00:00:00] Welcome to the course.
[00:00:04] Today we cover ...
```

## Notes

* Keep the charger connected. The Mac is kept awake during a run.
* English only. No speaker labels. Timestamps are per segment (a few seconds).
* Supported: .mp4 .mov .m4v .mkv .webm .avi
