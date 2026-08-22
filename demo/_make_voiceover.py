"""Generate GeneHus demo voiceover and mux into the application video."""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg

ROOT = Path(r"c:\Users\fresh\Desktop\GeneHus\genehus.github.io")
OUT = ROOT / "demo" / "video"
SCRIPT_MD = OUT / "GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md"
VIDEO_IN = OUT / "GeneHus_Clinician_Demo.mp4"
AUDIO_RAW = OUT / "_vo_raw.mp3"
AUDIO_PAD = OUT / "GeneHus_Clinician_Demo_voiceover.mp3"
VIDEO_OUT = OUT / "GeneHus_Clinician_Demo.mp4"
VIDEO_SILENT_BACKUP = OUT / "GeneHus_Clinician_Demo_silent.mp4"

# Professional clear male voice (British). Alternative African English: en-NG-AbeoNeural
VOICE = "en-GB-RyanNeural"
RATE = "-5%"
PITCH = "-2Hz"

# Timed segments aligned to the rebuilt ~87s demo.
# start = seconds from video start; text spoken after a short breath.
SEGMENTS: list[tuple[float, str]] = [
    (
        0.5,
        "This is GeneHus — a clinician preview for African-trained genomic and clinical risk stratification in aggressive prostate cancer.",
    ),
    (
        6.2,
        "The problem: African men face among the highest prostate-cancer mortality, and often present late. Hospitals still triage mainly on P-S-A and clinical judgement.",
    ),
    (
        12.8,
        "GeneHus is building a ranked hospital list that combines routine clinical inputs with an African genomic signal — so doctors can see who to review first, while staying in the loop.",
    ),
    (
        19.2,
        "This is the hospital clinician preview. Sample cases only — not a working diagnostic tool, and not for clinical use.",
    ),
    (
        24.2,
        "Inside the demo ward, patients are ranked by combined risk. At the top: a typical late presentation — very high P-S-A, high Gleason, advanced stage.",
    ),
    (
        31.5,
        "Lower on the list, a modest P-S-A with a genomic flag switched on — showing why P-S-A alone is not enough.",
    ),
    (
        37.5,
        "An unclear P-S-A case sits in the middle — the preview compares P-S-A alone with the GeneHus combined score.",
    ),
    (
        43.5,
        "A high-grade rising P-S-A case stays near the top of the queue — who to see first.",
    ),
    (
        49.5,
        "Back to the highest-risk sample. GeneHus suggests earlier staging and specialist review. The doctor decides next steps.",
    ),
    (
        55.5,
        "Clinicians can also enter a new sample case — age, P-S-A, Gleason, stage, family history, and a sample African genomic profile — then update the preview.",
    ),
    (
        65.2,
        "Honest status: this is a preview only. Working v-one is not built yet. No real patients. No M-A-D-C-a-P data in this screen. Not validated. Not Ghana F-D-A approved.",
    ),
    (
        74.0,
        "Nearest milestone: M-A-D-C-a-P permission, then v-one, then a hospital check versus P-S-A alone. Try the interactive demo at genehus.bio/demo. GeneHus — Kumasi, Ghana.",
    ),
]


SCRIPT_DOC = """# GeneHus Clinician Demo — Voiceover Script

**Video:** GeneHus_Clinician_Demo.mp4 (~87 seconds, 1600×900)
**Voice:** Microsoft neural TTS · en-GB-RyanNeural (clear application narration)
**Tone:** Calm, precise, investor/diligence-ready. No hype. Keep the disclaimer honest.
**Pronunciation notes in production:** say “P-S-A”, “M-A-D-C-a-P”, “F-D-A”, “v-one”.

---

## Full narration (spoken)

### 0:00 — Open
This is GeneHus — a clinician preview for African-trained genomic and clinical risk stratification in aggressive prostate cancer.

### 0:06 — Problem
The problem: African men face among the highest prostate-cancer mortality, and often present late. Hospitals still triage mainly on PSA and clinical judgement.

### 0:12 — Product
GeneHus is building a ranked hospital list that combines routine clinical inputs with an African genomic signal — so doctors can see who to review first, while staying in the loop.

### 0:19 — Gate
This is the hospital clinician preview. Sample cases only — not a working diagnostic tool, and not for clinical use.

### 0:24 — Highest-risk case
Inside the demo ward, patients are ranked by combined risk. At the top: a typical late presentation — very high PSA, high Gleason, advanced stage.

### 0:31 — Genomic flag / modest PSA
Lower on the list, a modest PSA with a genomic flag switched on — showing why PSA alone is not enough.

### 0:37 — Unclear PSA
An unclear PSA case sits in the middle — the preview compares PSA alone with the GeneHus combined score.

### 0:43 — High-grade case
A high-grade rising PSA case stays near the top of the queue — who to see first.

### 0:49 — Clinician in the loop
Back to the highest-risk sample. GeneHus suggests earlier staging and specialist review. The doctor decides next steps.

### 0:55 — New sample case
Clinicians can also enter a new sample case — age, PSA, Gleason, stage, family history, and a sample African genomic profile — then update the preview.

### 1:04 — Honest status
Honest status: this is a preview only. Working v1 is not built yet. No real patients. No MADCaP data in this screen. Not validated. Not Ghana FDA approved.

### 1:13 — Close
Nearest milestone: MADCaP permission, then v1, then a hospital check versus PSA alone. Try the interactive demo at genehus.bio/demo. GeneHus — Kumasi, Ghana.

---

## One-block script (for live recording)

This is GeneHus — a clinician preview for African-trained genomic and clinical risk stratification in aggressive prostate cancer.

The problem: African men face among the highest prostate-cancer mortality, and often present late. Hospitals still triage mainly on PSA and clinical judgement.

GeneHus is building a ranked hospital list that combines routine clinical inputs with an African genomic signal — so doctors can see who to review first, while staying in the loop.

This is the hospital clinician preview. Sample cases only — not a working diagnostic tool, and not for clinical use.

Inside the demo ward, patients are ranked by combined risk. At the top: a typical late presentation — very high PSA, high Gleason, advanced stage. Lower on the list, a modest PSA with a genomic flag switched on — showing why PSA alone is not enough. An unclear PSA case sits in the middle — the preview compares PSA alone with the GeneHus combined score. A high-grade rising PSA case stays near the top of the queue — who to see first.

Back to the highest-risk sample. GeneHus suggests earlier staging and specialist review. The doctor decides next steps.

Clinicians can also enter a new sample case — age, PSA, Gleason, stage, family history, and a sample African genomic profile — then update the preview.

Honest status: this is a preview only. Working v1 is not built yet. No real patients. No MADCaP data in this screen. Not validated. Not Ghana FDA approved.

Nearest milestone: MADCaP permission, then v1, then a hospital check versus PSA alone. Try the interactive demo at genehus.bio/demo. GeneHus — Kumasi, Ghana.

---

## Disclaimer (must stay on screen / in VO)

Sample data. Preview only. Not for clinical use. Not validated. Not Ghana FDA approved. Working v1 is not built yet.
"""


async def synth_segment(text: str, path: Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(str(path))


async def build_voice_track(video_duration: float) -> Path:
    work = OUT / "_vo_parts"
    if work.exists():
        import shutil

        shutil.rmtree(work)
    work.mkdir(parents=True)

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    part_files: list[tuple[float, Path]] = []
    for i, (start, text) in enumerate(SEGMENTS):
        part = work / f"part_{i:02d}.mp3"
        await synth_segment(text, part)
        part_files.append((start, part))
        print(f"  VO {start:5.1f}s  {text[:64]}...")

    # Build ffmpeg filter: delay each segment then amix
    # Use adelay in ms for each input
    inputs: list[str] = []
    filters = []
    for i, (start, part) in enumerate(part_files):
        inputs.extend(["-i", str(part)])
        delay_ms = int(start * 1000)
        filters.append(f"[{i}]adelay={delay_ms}|{delay_ms},volume=1[a{i}]")

    mix_in = "".join(f"[a{i}]" for i in range(len(part_files)))
    filters.append(
        f"{mix_in}amix=inputs={len(part_files)}:duration=longest:normalize=0[aout]"
    )
    filter_complex = ";".join(filters)

    mixed = work / "mixed.mp3"
    cmd = [
        ff,
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[aout]",
        "-t",
        f"{video_duration:.2f}",
        "-ar",
        "44100",
        "-ac",
        "1",
        str(mixed),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Pad/trim exact length to video
    cmd2 = [
        ff,
        "-y",
        "-i",
        str(mixed),
        "-af",
        f"apad=whole_dur={video_duration:.2f}",
        "-t",
        f"{video_duration:.2f}",
        "-ar",
        "44100",
        "-ac",
        "1",
        str(AUDIO_PAD),
    ]
    subprocess.run(cmd2, check=True, capture_output=True)
    return AUDIO_PAD


def video_duration(path: Path) -> float:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration" in line:
            # Duration: 00:01:27.08,
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise SystemExit("Could not read video duration")


def mux(video: Path, audio: Path, out: Path) -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    # Keep silent master once
    if not VIDEO_SILENT_BACKUP.exists():
        VIDEO_SILENT_BACKUP.write_bytes(video.read_bytes())
        print("backed up silent video ->", VIDEO_SILENT_BACKUP.name)

    src = VIDEO_SILENT_BACKUP if VIDEO_SILENT_BACKUP.exists() else video
    cmd = [
        ff,
        "-y",
        "-i",
        str(src),
        "-i",
        str(audio),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print("muxed", out, "mb", round(out.stat().st_size / 1e6, 2))


def main() -> None:
    SCRIPT_MD.write_text(SCRIPT_DOC, encoding="utf-8")
    print("wrote script", SCRIPT_MD)

    # Prefer silent backup as video source if already voiced
    src = VIDEO_SILENT_BACKUP if VIDEO_SILENT_BACKUP.exists() else VIDEO_IN
    if not src.exists():
        raise SystemExit(f"Missing video: {src}")
    dur = video_duration(src)
    print(f"video duration {dur:.2f}s from {src.name}")

    asyncio.run(build_voice_track(dur))
    print("wrote audio", AUDIO_PAD)

    mux(src, AUDIO_PAD, VIDEO_OUT)

    # Also write a standalone voiced copy at repo root for uploads
    root_copy = Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo.mp4")
    root_copy.write_bytes(VIDEO_OUT.read_bytes())
    print("copied", root_copy)


if __name__ == "__main__":
    main()
