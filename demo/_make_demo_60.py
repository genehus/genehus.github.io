"""
GeneHus clinician demo — careful timing

- Normal start cards (with voice from 0:00)
- Dashboard extended so voice + dashboard both end at exactly 1:12 (72.00s)
- End card: 2.00s, silent (no voice)
- Total: 74.00s
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

VOICE_END = 72.0   # 1:12 — voice + dashboard end here
END_SEC = 2.0      # silent end card
TOTAL_SEC = VOICE_END + END_SEC

# Normal start cards (intentional on-screen time; +settle in card())
OPEN_HOLDS = (2.3, 2.3, 2.1)

SCRIPT_MD = """# GeneHus Clinician Demo — timing

1. **0:00** voice starts with the normal start cards
2. **0:00–1:12** voice continues through start cards + clinician dashboard
3. **1:12** voice ends; dashboard ends at the same moment
4. **1:12–1:14** end card only — 2 seconds, no voice

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
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([exe, "-i", str(path)], capture_output=True, text=True)
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


def record_full_to_voice_end() -> Path:
    """Normal start cards, then dashboard until ~72s total raw (then pad/trim)."""
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    base = f"http://127.0.0.1:{PORT}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VW, "height": VH},
            device_scale_factor=1,
            record_video_dir=str(WORK),
            record_video_size={"width": VW, "height": VH},
        )
        page = context.new_page()

        def card(html: str, seconds: float, *, wrap_class: str = "") -> None:
            wrap_cls = f"wrap {wrap_class}".strip()
            page.set_content(
                f"""<!DOCTYPE html><html><head><meta charset="utf-8">
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
                <style>
                  html,body{{margin:0;height:100%;background:#111;color:#fff;font-family:Lato,Helvetica,sans-serif;overflow:hidden}}
                  .wrap{{height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:48px 72px;box-sizing:border-box;background:radial-gradient(ellipse at 50% 20%,#2c3439 0%,#111 70%)}}
                  .eyebrow{{font-size:18px;letter-spacing:.18em;text-transform:uppercase;color:#f88820;font-weight:700;margin-bottom:14px}}
                  h1{{font-family:Oswald,sans-serif;font-weight:600;font-size:52px;letter-spacing:.04em;text-transform:uppercase;margin:0 0 16px;line-height:1.15;max-width:1400px}}
                  p{{font-size:24px;color:#d8dee4;max-width:1100px;line-height:1.45;margin:0}}
                  .fine{{margin-top:18px;font-size:16px;color:#999;letter-spacing:.04em;text-transform:uppercase}}
                  .logo-plain{{margin-bottom:28px}}
                  .logo-plain img{{display:block;height:168px;width:auto;max-width:min(860px,78vw);object-fit:contain;background:transparent;
                    filter:drop-shadow(0 8px 18px rgba(0,0,0,.45)) drop-shadow(0 1px 0 rgba(255,255,255,.12))}}
                  .wrap-end .logo-plain{{margin-bottom:30px}}
                  .wrap-end .logo-plain img{{height:auto;width:min(1180px,70vw);max-height:260px;object-fit:contain;
                    filter:drop-shadow(0 12px 26px rgba(0,0,0,.55)) drop-shadow(0 2px 0 rgba(255,255,255,.14))}}
                  .wrap-end h1{{font-size:40px;margin-bottom:10px}}
                  .wrap-end p{{font-size:20px}}
                  .wrap-end .eyebrow{{font-size:16px;margin-bottom:16px}}
                </style></head><body><div class="{wrap_cls}">{html}</div></body></html>""",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(350)
            page.wait_for_timeout(int(seconds * 1000))

        open_logo = f"{base}/assets/genehus-logo-b5-white.png"

        # --- Normal start cards (voice plays over these) ---
        card(
            f'<div class="logo-plain"><img src="{open_logo}" alt="GeneHus"></div>'
            '<div class="eyebrow">Product demo</div>'
            "<h1>GeneHus clinician preview</h1>"
            "<p>African-trained genomic + clinical risk stratification for aggressive prostate cancer.</p>"
            '<div class="fine">Sample data only · Not for clinical use</div>',
            OPEN_HOLDS[0],
        )
        card(
            '<div class="eyebrow">The problem</div>'
            "<h1>PSA alone misses who needs attention first</h1>"
            "<p>African men face among the highest prostate-cancer mortality and often present late.</p>"
            '<div class="fine">Ghana beachhead · tertiary hospitals</div>',
            OPEN_HOLDS[1],
        )
        card(
            '<div class="eyebrow">The product</div>'
            "<h1>A ranked hospital list for the clinician</h1>"
            "<p>Combine clinical inputs with an African genomic signal. The doctor stays in the loop.</p>"
            '<div class="fine">Hospital or lab sequences · GeneHus analyses</div>',
            OPEN_HOLDS[2],
        )

        # --- Dashboard extended to fill through 1:12 ---
        # Open ≈ 3*(0.35+hold) ≈ 8.4s; leave ~63s for dashboard before pad/trim to 72
        page.goto(f"{base}/demo/app.html", wait_until="domcontentloaded")
        page.wait_for_selector("#queue-list .queue-item")
        page.wait_for_timeout(300)

        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(22000)
        page.locator('[data-id="benjamin"]').click()
        page.wait_for_timeout(14000)
        page.locator('[data-id="ibrahim"]').click()
        page.wait_for_timeout(14000)
        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(14000)

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
    print(f"  voice trimmed {media_duration(out):.2f}s (want {seconds:.2f}s)")


def mux_voiced(video: Path, audio: Path, out: Path, seconds: float) -> None:
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
    print(f"  voiced body {got:.2f}s (ends at 1:12)")


def concat_parts(body: Path, end: Path, out: Path) -> None:
    end_a = OUT / "_end_silent_a.mp4"
    run([
        ff(), "-y",
        "-i", str(end),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{END_SEC:.2f}",
        "-shortest",
        "-movflags", "+faststart",
        str(end_a),
    ])
    lst = OUT / "_concat.txt"
    lst.write_text(
        f"file '{body.resolve().as_posix()}'\nfile '{end_a.resolve().as_posix()}'\n",
        encoding="utf-8",
    )
    run([
        ff(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", "-movflags", "+faststart", str(out),
    ])
    got = media_duration(out)
    print(f"  final {got:.2f}s (want {TOTAL_SEC:.2f}s)")
    if abs(got - TOTAL_SEC) > 0.15:
        raise SystemExit(f"Final duration {got:.2f}s != {TOTAL_SEC:.2f}s")
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
        print("1) Record start cards + dashboard...")
        webm = record_full_to_voice_end()
        body_silent = OUT / "_body72.mp4"
        webm_to_exact(webm, body_silent, VOICE_END)

        print("2) Trim voice to 1:12...")
        voice72 = OUT / "_voice72.ogg"
        trim_voice(VOICE_SRC, voice72, VOICE_END)

        print("3) Mux voice from start through 1:12...")
        body_voiced = OUT / "_body72_voiced.mp4"
        mux_voiced(body_silent, voice72, body_voiced, VOICE_END)

        print("4) End card 2s silent...")
        end_card = OUT / "_end2.mp4"
        make_end_card(end_card, END_SEC)

        print("5) Concat...")
        final = OUT / "GeneHus_Clinician_Demo.mp4"
        concat_parts(body_voiced, end_card, final)

        shutil.copy2(body_silent, OUT / "GeneHus_Clinician_Demo_silent.mp4")
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
            "_body72.mp4", "_body72_voiced.mp4", "_end2.mp4", "_voice72.ogg",
            "_raw_tmp.mp4", "_end_silent_a.mp4", "_concat.txt",
        ):
            p = OUT / name
            if p.exists():
                p.unlink()


if __name__ == "__main__":
    main()
