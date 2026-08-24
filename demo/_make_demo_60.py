"""
GeneHus clinician demo — careful timing
1. Dashboard + voice: exactly 72.00s (1:12)
2. End card: exactly 2.00s, silent
3. Total: 74.00s
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
VOICE_SRC = Path(r"c:\Users\fresh\Desktop\GeneHus\Demo\real_voice.ogg")
PORT = 8883
VW, VH = 1920, 1080
RW, RH = 3840, 2160
POSTER_W, POSTER_H = 1920, 1080

DASH_SEC = 72.0   # 1:12 — voice + dashboard end here
END_SEC = 2.0     # silent end card
TOTAL_SEC = DASH_SEC + END_SEC

SCRIPT_MD = """# GeneHus Clinician Demo — timing

1. **0:00–1:12** clinician dashboard + real voice (both end at 1:12 strictly)
2. **1:12–1:14** end card only — 2 seconds, no voice

**Audio:** `Demo/real_voice.ogg` trimmed to exactly 72.00s
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


def ff() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


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


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def make_poster() -> None:
    src = ROOT / "assets" / "AM.png"
    im = Image.open(src).convert("RGBA")
    canvas = Image.new("RGB", (POSTER_W, POSTER_H), (17, 17, 17))
    fitted = ImageOps.contain(im, (POSTER_W - 40, POSTER_H - 40))
    canvas.paste(fitted, ((POSTER_W - fitted.width) // 2, (POSTER_H - fitted.height) // 2), fitted)
    canvas.save(ROOT / "assets" / "AM-poster.png")
    canvas.save(OUT / "poster.png")
    print("poster updated")


def record_dashboard() -> Path:
    """Record clinician app only; aim slightly under 72s then pad/trim."""
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    base = f"http://127.0.0.1:{PORT}"

    # Four holds ≈ 70s intentional; ~2s load → ~72s raw
    holds = [22.0, 16.0, 16.0, 16.0]

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
        page.wait_for_timeout(300)

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


def webm_to_exact(webm: Path, out: Path, seconds: float) -> None:
    raw = OUT / "_raw_tmp.mp4"
    run([
        ff(), "-y", "-i", str(webm),
        "-vf", f"scale={RW}:{RH}:flags=lanczos,setsar=1",
        *h264_args(), "-an", str(raw),
    ])
    dur = media_duration(raw)
    print(f"  raw {dur:.2f}s -> exact {seconds:.2f}s")
    if dur >= seconds:
        run([
            ff(), "-y", "-i", str(raw), "-t", f"{seconds:.2f}",
            *h264_args(), "-an", str(out),
        ])
    else:
        pad = seconds - dur
        run([
            ff(), "-y", "-i", str(raw),
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
            "-t", f"{seconds:.2f}",
            *h264_args(), "-an", str(out),
        ])
    raw.unlink(missing_ok=True)
    got = media_duration(out)
    if abs(got - seconds) > 0.08:
        raise SystemExit(f"Duration miss: {out.name} is {got:.2f}s, want {seconds:.2f}s")
    print(f"  ok {out.name} {got:.2f}s")


def make_end_card(out: Path, seconds: float) -> None:
    """2s silent end card via Playwright record."""
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    base = f"http://127.0.0.1:{PORT}"
    end_logo = f"{base}/assets/GeneHus_Logo_white.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VW, "height": VH},
            device_scale_factor=1,
            record_video_dir=str(WORK),
            record_video_size={"width": VW, "height": VH},
        )
        page = context.new_page()
        page.set_content(
            f"""<!DOCTYPE html><html><head><meta charset="utf-8">
            <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&family=Oswald:wght@600&display=swap" rel="stylesheet">
            <style>
              html,body{{margin:0;height:100%;background:#111;color:#fff;font-family:Lato,sans-serif;overflow:hidden}}
              .wrap{{height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
                background:radial-gradient(ellipse at 50% 20%,#2c3439 0%,#111 70%);padding:48px}}
              img{{width:min(1000px,68vw);height:auto;max-height:220px;object-fit:contain;
                filter:drop-shadow(0 12px 26px rgba(0,0,0,.55))}}
              .eyebrow{{margin-top:22px;font-size:15px;letter-spacing:.16em;text-transform:uppercase;color:#f88820;font-weight:700}}
              h1{{font-family:Oswald,sans-serif;font-size:36px;letter-spacing:.04em;text-transform:uppercase;margin:10px 0 8px}}
              p{{font-size:18px;color:#d8dee4;margin:0}}
            </style></head><body><div class="wrap">
              <img src="{end_logo}" alt="GeneHus">
              <div class="eyebrow">GeneHus · Kumasi, Ghana</div>
              <h1>genehus.bio/demo</h1>
              <p>Try the clinician preview</p>
            </div></body></html>""",
            wait_until="domcontentloaded",
        )
        # Record slightly longer than 2s so trim is clean after encode overhead
        page.wait_for_timeout(int((seconds + 1.2) * 1000))
        page.close()
        context.close()
        browser.close()

    videos = sorted(WORK.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise SystemExit("No end-card video")
    webm_to_exact(videos[0], out, seconds)
    shutil.rmtree(WORK, ignore_errors=True)


def trim_voice(src: Path, out: Path, seconds: float) -> None:
    run([
        ff(), "-y", "-i", str(src),
        "-t", f"{seconds:.2f}",
        "-ar", "48000", "-ac", "1",
        str(out),
    ])
    got = media_duration(out)
    print(f"  voice trimmed {got:.2f}s (want {seconds:.2f}s)")


def mux_dash(video: Path, audio: Path, out: Path, seconds: float) -> None:
    run([
        ff(), "-y",
        "-i", str(video),
        "-i", str(audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{seconds:.2f}",
        "-movflags", "+faststart",
        str(out),
    ])
    got = media_duration(out)
    if abs(got - seconds) > 0.08:
        raise SystemExit(f"Mux miss: {got:.2f}s want {seconds:.2f}s")
    print(f"  voiced dashboard {got:.2f}s")


def concat_parts(dash: Path, end: Path, out: Path) -> None:
    """Concat voiced dashboard + silent end card; end has no audio so add silent aac."""
    end_a = OUT / "_end_silent_a.mp4"
    # Give end card a silent audio track so concat is clean
    run([
        ff(), "-y",
        "-i", str(end),
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=mono:sample_rate=48000",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{END_SEC:.2f}",
        "-shortest",
        "-movflags", "+faststart",
        str(end_a),
    ])
    lst = OUT / "_concat.txt"
    lst.write_text(
        f"file '{dash.resolve().as_posix()}'\nfile '{end_a.resolve().as_posix()}'\n",
        encoding="utf-8",
    )
    run([
        ff(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", "-movflags", "+faststart", str(out),
    ])
    got = media_duration(out)
    print(f"  final {got:.2f}s (want {TOTAL_SEC:.2f}s)")
    if abs(got - TOTAL_SEC) > 0.15:
        raise SystemExit(f"Final duration {got:.2f}s ≠ {TOTAL_SEC:.2f}s")
    end_a.unlink(missing_ok=True)
    lst.unlink(missing_ok=True)


def main() -> None:
    if not VOICE_SRC.exists():
        raise SystemExit(f"Missing {VOICE_SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(SCRIPT_MD, encoding="utf-8")
    shutil.copy2(VOICE_SRC, OUT / "real_voice.ogg")
    make_poster()
    os.chdir(ROOT)
    httpd = serve()
    time.sleep(0.4)
    try:
        print("1) Record dashboard…")
        webm = record_dashboard()
        dash_silent = OUT / "_dash72.mp4"
        webm_to_exact(webm, dash_silent, DASH_SEC)

        print("2) Trim voice to 1:12…")
        voice72 = OUT / "_voice72.ogg"
        trim_voice(VOICE_SRC, voice72, DASH_SEC)

        print("3) Mux voice onto dashboard (ends 1:12)…")
        dash_voiced = OUT / "_dash72_voiced.mp4"
        mux_dash(dash_silent, voice72, dash_voiced, DASH_SEC)

        print("4) End card 2s silent…")
        end_card = OUT / "_end2.mp4"
        make_end_card(end_card, END_SEC)

        print("5) Concat…")
        final = OUT / "GeneHus_Clinician_Demo.mp4"
        concat_parts(dash_voiced, end_card, final)

        # Keep silent master = dashboard only (72s) for rebuilds
        shutil.copy2(dash_silent, OUT / "GeneHus_Clinician_Demo_silent.mp4")

        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo.mp4").write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\Demo\GeneHus_Clinician_Demo.mp4").write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(
            SCRIPT_MD, encoding="utf-8"
        )
        print(f"DONE {final} {media_duration(final):.2f}s mb={final.stat().st_size/1e6:.2f}")
    finally:
        httpd.shutdown()
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        for name in (
            "_dash72.mp4", "_dash72_voiced.mp4", "_end2.mp4", "_voice72.ogg",
            "_raw_tmp.mp4", "_end_silent_a.mp4", "_concat.txt",
        ):
            p = OUT / name
            if p.exists():
                p.unlink()


if __name__ == "__main__":
    main()
