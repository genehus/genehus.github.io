"""
Build GeneHus clinician demo: exactly 60.00s, AM.png branding,
single West-African English voiceover (no overlapping tracks).
"""
from __future__ import annotations

import asyncio
import http.server
import os
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

ROOT = Path(r"c:\Users\fresh\Desktop\GeneHus\genehus.github.io")
OUT = ROOT / "demo" / "video"
WORK = OUT / "_work"
PORT = 8878
W, H = 1600, 900
TARGET_SEC = 60.0

# Closest available West African English neural voice (no en-GH in Edge TTS)
VOICE = "en-NG-AbeoNeural"
RATE = "-8%"
PITCH = "+0Hz"

NARRATION = (
    "This is GeneHus — a clinician preview for African-trained genomic and clinical "
    "risk stratification in aggressive prostate cancer. "
    "African men face high prostate-cancer mortality and often present late. "
    "Hospitals still triage mainly on P-S-A. "
    "GeneHus ranks who to see first using clinical inputs plus an African genomic signal — "
    "while the doctor stays in the loop. "
    "Sample cases only. Not for clinical use. "
    "Late presentations rise to the top of the queue. "
    "A modest P-S-A with a genomic flag shows why P-S-A alone is not enough. "
    "Enter a new sample case and update the preview. "
    "Honest status: working v-one is not built yet. Not validated. Not Ghana F-D-A approved. "
    "Next: M-A-D-C-a-P permission, then v-one, then a hospital check versus P-S-A alone. "
    "GeneHus — genehus.bio/demo — Kumasi, Ghana."
)

SCRIPT_MD = """# GeneHus Clinician Demo — Voiceover Script (60 seconds)

**Voice:** West African English neural TTS (`en-NG-AbeoNeural`) — closest available Ghana/West Africa accent in Edge TTS.
**Length:** exactly 60.00 seconds · single continuous track (no overlapping voices)

---

This is GeneHus — a clinician preview for African-trained genomic and clinical risk stratification in aggressive prostate cancer. African men face high prostate-cancer mortality and often present late. Hospitals still triage mainly on PSA. GeneHus ranks who to see first using clinical inputs plus an African genomic signal — while the doctor stays in the loop. Sample cases only. Not for clinical use. Late presentations rise to the top of the queue. A modest PSA with a genomic flag shows why PSA alone is not enough. Enter a new sample case and update the preview. Honest status: working v1 is not built yet. Not validated. Not Ghana FDA approved. Next: MADCaP permission, then v1, then a hospital check versus PSA alone. GeneHus — genehus.bio/demo — Kumasi, Ghana.
"""


def serve() -> socketserver.TCPServer:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # noqa: ANN002
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def make_poster() -> None:
    src = ROOT / "assets" / "AM.png"
    im = Image.open(src).convert("RGBA")
    canvas = Image.new("RGB", (W, H), (17, 17, 17))
    fitted = ImageOps.contain(im, (W - 160, H - 160))
    canvas.paste(fitted, ((W - fitted.width) // 2, (H - fitted.height) // 2), fitted)
    canvas.save(ROOT / "assets" / "AM-poster.png")
    canvas.save(OUT / "poster.png")


def record_demo() -> Path:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    base = f"http://127.0.0.1:{PORT}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
            record_video_dir=str(WORK),
            record_video_size={"width": W, "height": H},
        )
        page = context.new_page()

        def card(html: str, seconds: float) -> None:
            page.set_content(
                f"""<!DOCTYPE html><html><head><meta charset="utf-8">
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
                <style>
                  html,body{{margin:0;height:100%;background:#111;color:#fff;font-family:Lato,Helvetica,sans-serif;overflow:hidden}}
                  .wrap{{height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:36px 52px;box-sizing:border-box;background:radial-gradient(ellipse at 50% 20%,#2c3439 0%,#111 70%)}}
                  .eyebrow{{font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#f88820;font-weight:700;margin-bottom:14px}}
                  h1{{font-family:Oswald,sans-serif;font-weight:600;font-size:44px;letter-spacing:.04em;text-transform:uppercase;margin:0 0 14px;line-height:1.15;max-width:1000px}}
                  p{{font-size:19px;color:#d8dee4;max-width:820px;line-height:1.45;margin:0}}
                  .fine{{margin-top:20px;font-size:12px;color:#999;letter-spacing:.04em;text-transform:uppercase}}
                  .logo-frame{{width:min(720px,86vw);background:#ececec;padding:14px 18px;margin-bottom:18px;box-sizing:border-box}}
                  .logo-frame img{{display:block;width:100%;height:auto;max-height:260px;object-fit:contain}}
                </style></head><body><div class="wrap">{html}</div></body></html>""",
                wait_until="networkidle",
            )
            page.wait_for_timeout(int(seconds * 1000))

        logo = f"{base}/assets/AM.png"
        logo_block = f'<div class="logo-frame"><img src="{logo}" alt="GeneHus"></div>'

        # Timed for ~60s total including navigation overhead
        card(
            logo_block
            + '<div class="eyebrow">Product demo</div>'
            "<h1>GeneHus clinician preview</h1>"
            "<p>African-trained genomic + clinical risk stratification for aggressive prostate cancer.</p>"
            '<div class="fine">Sample data only · Not for clinical use</div>',
            4.0,
        )
        card(
            '<div class="eyebrow">The problem</div>'
            "<h1>PSA alone misses who needs attention first</h1>"
            "<p>African men face among the highest prostate-cancer mortality and often present late.</p>"
            '<div class="fine">Ghana beachhead · Korle Bu / KATH</div>',
            4.0,
        )
        card(
            '<div class="eyebrow">The product</div>'
            "<h1>A ranked hospital list for the clinician</h1>"
            "<p>Combine clinical inputs with an African genomic signal. The doctor stays in the loop.</p>"
            '<div class="fine">Hospital or lab sequences · GeneHus analyses</div>',
            4.0,
        )

        page.goto(f"{base}/demo/", wait_until="networkidle")
        page.wait_for_timeout(3000)

        page.click("#enter-btn")
        page.wait_for_url("**/demo/app.html")
        page.wait_for_selector("#queue-list .queue-item")
        page.wait_for_timeout(4500)

        page.locator('[data-id="benjamin"]').click()
        page.wait_for_timeout(4000)

        page.locator('[data-id="ibrahim"]').click()
        page.wait_for_timeout(3500)

        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(3500)

        page.click("#new-case-btn")
        page.wait_for_timeout(1500)
        page.fill('input[name="psa"]', "18")
        page.select_option('select[name="gleason"]', "8")
        page.check('input[name="genomic"]')
        page.wait_for_timeout(800)
        page.click('button[type="submit"]')
        page.wait_for_timeout(4000)

        card(
            '<div class="eyebrow">Honest status</div>'
            "<h1>Preview only — working v1 is not built yet</h1>"
            "<p>No real patients. Not validated. Not Ghana FDA approved. Next: MADCaP permission, then v1.</p>",
            4.5,
        )
        card(
            logo_block
            + '<div class="eyebrow">GeneHus · Kumasi, Ghana</div>'
            "<h1>genehus.bio/demo</h1>"
            "<p>Try the clinician preview · safoduker@genehus.bio</p>",
            4.0,
        )

        page.wait_for_timeout(800)
        page.close()
        context.close()
        browser.close()

    videos = sorted(WORK.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise SystemExit("No video recorded")
    return videos[0]


def media_duration(path: Path) -> float:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise SystemExit(f"No duration for {path}")


def to_exact_silent_mp4(webm: Path) -> Path:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = OUT / "_raw60.mp4"
    silent = OUT / "GeneHus_Clinician_Demo_silent.mp4"
    # First encode, then force exact 60.00s (trim or pad last frame)
    subprocess.run(
        [
            ff,
            "-y",
            "-i",
            str(webm),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(raw),
        ],
        check=True,
        capture_output=True,
    )
    dur = media_duration(raw)
    print(f"raw video {dur:.2f}s")
    if dur >= TARGET_SEC:
        # trim to exactly 60s
        subprocess.run(
            [
                ff,
                "-y",
                "-i",
                str(raw),
                "-t",
                f"{TARGET_SEC:.2f}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                str(silent),
            ],
            check=True,
            capture_output=True,
        )
    else:
        pad = TARGET_SEC - dur
        subprocess.run(
            [
                ff,
                "-y",
                "-i",
                str(raw),
                "-vf",
                f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
                "-t",
                f"{TARGET_SEC:.2f}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                str(silent),
            ],
            check=True,
            capture_output=True,
        )
    print(f"silent exact {media_duration(silent):.2f}s")
    return silent


async def make_voice(out_mp3: Path) -> None:
    # One continuous track — never amix multiple overlapping clips
    communicate = edge_tts.Communicate(NARRATION, VOICE, rate=RATE, pitch=PITCH)
    raw = OUT / "_vo_full.mp3"
    await communicate.save(str(raw))
    dur = media_duration(raw)
    print(f"voice raw {dur:.2f}s")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    if dur > TARGET_SEC - 0.3:
        # slightly speed up to fit under 60s with a short tail
        tempo = dur / (TARGET_SEC - 0.8)
        # atempo only supports 0.5–2.0
        tempo = max(0.5, min(2.0, tempo))
        af = f"atempo={tempo:.4f},apad=whole_dur={TARGET_SEC:.2f}"
    else:
        af = f"apad=whole_dur={TARGET_SEC:.2f}"
    subprocess.run(
        [
            ff,
            "-y",
            "-i",
            str(raw),
            "-af",
            af,
            "-t",
            f"{TARGET_SEC:.2f}",
            "-ar",
            "44100",
            "-ac",
            "1",
            str(out_mp3),
        ],
        check=True,
        capture_output=True,
    )
    print(f"voice exact {media_duration(out_mp3):.2f}s")


def mux(silent: Path, audio: Path, out: Path) -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ff,
            "-y",
            "-i",
            str(silent),
            "-i",
            str(audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{TARGET_SEC:.2f}",
            "-movflags",
            "+faststart",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    print(f"final {out.name} {media_duration(out):.2f}s  mb={out.stat().st_size/1e6:.2f}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(SCRIPT_MD, encoding="utf-8")
    make_poster()
    os.chdir(ROOT)
    httpd = serve()
    time.sleep(0.4)
    try:
        webm = record_demo()
        print("recorded", webm)
        silent = to_exact_silent_mp4(webm)
        audio = OUT / "GeneHus_Clinician_Demo_voiceover.mp3"
        asyncio.run(make_voice(audio))
        final = OUT / "GeneHus_Clinician_Demo.mp4"
        mux(silent, audio, final)
        # drop old webm source from page; keep a 60s webm optional
        webm_out = OUT / "GeneHus_Clinician_Demo.webm"
        if webm_out.exists():
            webm_out.unlink()
        root_copy = Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo.mp4")
        root_copy.write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(
            SCRIPT_MD, encoding="utf-8"
        )
        print("copied to Desktop GeneHus")
    finally:
        httpd.shutdown()
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        for tmp in ("_raw60.mp4", "_vo_full.mp3"):
            p = OUT / tmp
            if p.exists():
                p.unlink()


if __name__ == "__main__":
    main()
