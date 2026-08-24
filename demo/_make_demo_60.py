"""
GeneHus clinician demo — dashboard only + real_voice.ogg
- No open/close title cards
- Voice starts at video start and ends with the clinician dashboard
"""
from __future__ import annotations

import http.server
import os
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

ROOT = Path(r"c:\Users\fresh\Desktop\GeneHus\genehus.github.io")
OUT = ROOT / "demo" / "video"
WORK = OUT / "_work"
VOICE = Path(r"c:\Users\fresh\Desktop\GeneHus\Demo\real_voice.ogg")
PORT = 8882
VW, VH = 1920, 1080
RW, RH = 3840, 2160
POSTER_W, POSTER_H = 1920, 1080

SCRIPT_MD = """# GeneHus Clinician Demo — with real voice

**Audio:** `Demo/real_voice.ogg` (starts at video start; ends with clinician dashboard)
**Video:** clinician preview dashboard only — no title cards before/after
"""


def serve() -> socketserver.TCPServer:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # noqa: ANN002
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def media_duration(path: Path) -> float:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise SystemExit(f"No duration for {path}")


def make_poster() -> None:
    src = ROOT / "assets" / "AM.png"
    im = Image.open(src).convert("RGBA")
    canvas = Image.new("RGB", (POSTER_W, POSTER_H), (17, 17, 17))
    fitted = ImageOps.contain(im, (POSTER_W - 40, POSTER_H - 40))
    canvas.paste(fitted, ((POSTER_W - fitted.width) // 2, (POSTER_H - fitted.height) // 2), fitted)
    canvas.save(ROOT / "assets" / "AM-poster.png")
    canvas.save(OUT / "poster.png")
    print("poster updated from AM.png banner")


def h264_args() -> list[str]:
    return [
        "-c:v", "libx264",
        "-preset", "medium",
        "-qp", "16",
        "-profile:v", "high",
        "-level", "5.1",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]


def record_dashboard(target_sec: float) -> Path:
    """Record only the clinician app — length ≈ target_sec (voice length)."""
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    base = f"http://127.0.0.1:{PORT}"

    # Budget holds so raw ≈ target (leave ~2s for load/overhead)
    hold = max(8.0, (target_sec - 2.0) / 4.0)
    holds = [hold * 1.15, hold * 0.95, hold * 0.95, hold * 0.95]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VW, "height": VH},
            device_scale_factor=1,
            record_video_dir=str(WORK),
            record_video_size={"width": VW, "height": VH},
        )
        page = context.new_page()

        page.goto(f"{base}/demo/app.html", wait_until="domcontentloaded")
        page.wait_for_selector("#queue-list .queue-item")
        page.wait_for_timeout(400)

        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(int(holds[0] * 1000))

        page.locator('[data-id="benjamin"]').click()
        page.wait_for_timeout(int(holds[1] * 1000))
        page.locator('[data-id="ibrahim"]').click()
        page.wait_for_timeout(int(holds[2] * 1000))
        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(int(holds[3] * 1000))

        page.close()
        context.close()
        browser.close()

    videos = sorted(WORK.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise SystemExit("No video recorded")
    return videos[0]


def to_silent_mp4(webm: Path, target_sec: float) -> Path:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = OUT / "_raw_dash.mp4"
    silent = OUT / "GeneHus_Clinician_Demo_silent.mp4"
    subprocess.run(
        [
            ff, "-y", "-i", str(webm),
            "-vf", f"scale={RW}:{RH}:flags=lanczos,setsar=1",
            *h264_args(),
            "-an", str(raw),
        ],
        check=True, capture_output=True,
    )
    dur = media_duration(raw)
    print(f"raw dashboard {dur:.2f}s (target {target_sec:.2f}s)")
    if dur >= target_sec:
        cmd = [
            ff, "-y", "-i", str(raw), "-t", f"{target_sec:.2f}",
            *h264_args(), "-an", str(silent),
        ]
    else:
        pad = target_sec - dur
        cmd = [
            ff, "-y", "-i", str(raw),
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
            "-t", f"{target_sec:.2f}",
            *h264_args(), "-an", str(silent),
        ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"silent exact {media_duration(silent):.2f}s 4K")
    if raw.exists():
        raw.unlink()
    return silent


def mux_voice(silent: Path, voice: Path, out: Path, target_sec: float) -> None:
    """Voice from t=0; cut both streams at target_sec (end of dashboard)."""
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ff, "-y",
            "-i", str(silent),
            "-i", str(voice),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{target_sec:.2f}",
            "-movflags", "+faststart",
            str(out),
        ],
        check=True, capture_output=True,
    )
    print(f"final {out.name} {media_duration(out):.2f}s mb={out.stat().st_size/1e6:.2f} (voiced)")


def main() -> None:
    if not VOICE.exists():
        raise SystemExit(f"Missing voice file: {VOICE}")
    voice_sec = media_duration(VOICE)
    print(f"voice {voice_sec:.2f}s")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(SCRIPT_MD, encoding="utf-8")
    shutil.copy2(VOICE, OUT / "real_voice.ogg")
    make_poster()
    os.chdir(ROOT)
    httpd = serve()
    time.sleep(0.4)
    try:
        webm = record_dashboard(voice_sec)
        print("recorded", webm)
        silent = to_silent_mp4(webm, voice_sec)
        final = OUT / "GeneHus_Clinician_Demo.mp4"
        mux_voice(silent, VOICE, final, voice_sec)
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo.mp4").write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\Demo\GeneHus_Clinician_Demo.mp4").write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(
            SCRIPT_MD, encoding="utf-8"
        )
    finally:
        httpd.shutdown()
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
