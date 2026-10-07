#!/usr/bin/env python3
"""
Transcribe one local video to a timestamped text file on the Desktop.

Engine: mlx-whisper (OpenAI Whisper large-v3-turbo on Apple Silicon GPU).
Usage:  make start   (then paste or drag the video file into the terminal)
Output: ~/Desktop/<video_name>_transcript.txt  (overwritten if it exists)
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

MODEL = "mlx-community/whisper-large-v3-turbo"
LANGUAGE = "en"
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
DESKTOP = Path.home() / "Desktop"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def check_env() -> None:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        sys.exit("ERROR: needs a Mac with Apple Silicon (M1 or newer). Run `make init` first.")
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"ERROR: {tool} not found. Run `make init` first.")
    if not DESKTOP.is_dir():
        sys.exit(f"ERROR: Desktop folder not found: {DESKTOP}")


def clean_path(raw: str) -> Path:
    """Handle paths pasted or dragged into the macOS terminal."""
    p = raw.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "'\"":
        p = p[1:-1]
    else:
        p = p.replace("\\ ", " ").replace("\\(", "(").replace("\\)", ")") \
             .replace("\\&", "&").replace("\\'", "'")
    return Path(p).expanduser().resolve()


def ask_video() -> Path:
    while True:
        try:
            raw = input("\nDrag the video here (or paste its path) and press Enter:\n> ")
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nCancelled.")
        if not raw.strip():
            continue
        path = clean_path(raw)
        if not path.is_file():
            print(f"Not found: {path}")
        elif path.suffix.lower() not in VIDEO_EXTS:
            print(f"Not a supported video ({', '.join(sorted(VIDEO_EXTS))}): {path.name}")
        else:
            return path


def probe_duration(path: Path) -> float:
    audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    if audio.returncode != 0 or not audio.stdout.strip():
        sys.exit(f"ERROR: no audio track in {path.name} (or file is unreadable).")
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(dur.stdout.strip())


def clean_segments(segments: list[dict]) -> list[dict]:
    """Drop empty segments and merge consecutive duplicates (Whisper loop artifact)."""
    out: list[dict] = []
    for s in segments:
        text = " ".join(s["text"].split())
        if not text:
            continue
        if out and text.lower() == out[-1]["text"].lower():
            out[-1]["end"] = float(s["end"])
            continue
        out.append({"start": float(s["start"]), "end": float(s["end"]), "text": text})
    return out


def transcribe(path: Path) -> list[dict]:
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(path),
        path_or_hf_repo=MODEL,
        language=LANGUAGE,
        task="transcribe",
        condition_on_previous_text=False,  # prevents repetition loops on long audio
        verbose=False,                     # progress bar only
    )
    return clean_segments(result["segments"])


def write_transcript(video: Path, segs: list[dict], duration: float, out: Path) -> None:
    header = (
        f"SOURCE: {video.name}\n"
        f"DURATION: {ts(duration)}\n"
        f"LANGUAGE: English\n"
        f"MODEL: {MODEL}\n"
        f"SEGMENTS: {len(segs)}\n"
        f"FORMAT: one line per segment, [HH:MM:SS] = start time in the video\n"
        f"---\n"
    )
    body = "\n".join(f"[{ts(s['start'])}] {s['text']}" for s in segs) + "\n"
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(header + body, encoding="utf-8")
    tmp.replace(out)


def main() -> int:
    check_env()
    video = ask_video()
    out = DESKTOP / f"{video.stem}_transcript.txt"
    duration = probe_duration(video)

    log(f"START {video.name} [{ts(duration)}]")
    t0 = time.time()
    segs = transcribe(video)
    wall = time.time() - t0
    if not segs:
        sys.exit("ERROR: no speech detected.")

    write_transcript(video, segs, duration, out)
    log(f"DONE in {ts(wall)} ({duration / wall:.1f}x realtime, {len(segs)} lines)")
    log(f"SAVED {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
