"""
GeneHus clinician demo — 60.00s
- Opening logo: transparent white (website style)
- Closing logo: GeneHus_Logo_ (white-on-transparent)
- Voice: British English neural (closer to Ghanaian Standard English than Nigerian)
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
PORT = 8880
# Record 4K UHD: 1080p layout at 2x device scale → sharp 3840×2160 capture
VW, VH = 1920, 1080
RW, RH = 3840, 2160
POSTER_W, POSTER_H = 1920, 1080
TARGET_SEC = 60.0

# Ghanaian Standard English is closer to British than Nigerian; Edge TTS has no en-GH.
VOICE = "en-GB-RyanNeural"
RATE = "-12%"  # steadier, broadcast-like Ghanaian delivery
PITCH = "-1Hz"

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

**Voice:** `en-GB-RyanNeural` (British English neural) — chosen because Ghanaian Standard English is closer to British than Nigerian, and Edge TTS has no `en-GH` voice.
**Length:** exactly 60.00 seconds · single continuous track

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
    """16:9 preview poster from AM.png banner (page thumbnail only; video open card unchanged)."""
    src = ROOT / "assets" / "AM.png"
    im = Image.open(src).convert("RGBA")
    canvas = Image.new("RGB", (POSTER_W, POSTER_H), (17, 17, 17))
    fitted = ImageOps.contain(im, (POSTER_W - 40, POSTER_H - 40))
    canvas.paste(fitted, ((POSTER_W - fitted.width) // 2, (POSTER_H - fitted.height) // 2), fitted)
    canvas.save(ROOT / "assets" / "AM-poster.png")
    canvas.save(OUT / "poster.png")
    print("poster updated from AM.png banner")


def record_demo() -> Path:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    base = f"http://127.0.0.1:{PORT}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VW, "height": VH},
            device_scale_factor=2,
            record_video_dir=str(WORK),
            record_video_size={"width": RW, "height": RH},
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
                wait_until="networkidle",
            )
            page.wait_for_timeout(int(seconds * 1000))

        # Website-style white transparent logo for open
        open_logo = f"{base}/assets/genehus-logo-b5-white.png"
        # GeneHus_Logo_ converted to white transparent for close
        end_logo = f"{base}/assets/GeneHus_Logo_white.png"

        card(
            f'<div class="logo-plain"><img src="{open_logo}" alt="GeneHus"></div>'
            '<div class="eyebrow">Product demo</div>'
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
        # Last card: GeneHus_Logo_ — sharper mid size + 3D shadow (CSS)
        card(
            f'<div class="logo-plain logo-end">'
            f'<img src="{end_logo}" alt="GeneHus" '
            f'style="width:min(1180px,70vw);height:auto;max-height:260px;object-fit:contain;display:block">'
            f"</div>"
            '<div class="eyebrow">GeneHus · Kumasi, Ghana</div>'
            "<h1>genehus.bio/demo</h1>"
            "<p>Try the clinician preview · safoduker@genehus.bio</p>",
            4.5,
            wrap_class="wrap-end",
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


def h264_args() -> list[str]:
    """Solid 4K bitrate (~12 Mbps, under GitHub 100MB limit for 60s)."""
    return [
        "-c:v", "libx264",
        "-preset", "medium",
        "-b:v", "12M",
        "-minrate", "8M",
        "-maxrate", "18M",
        "-bufsize", "24M",
        "-profile:v", "high",
        "-level", "5.1",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]


def to_exact_silent_mp4(webm: Path) -> Path:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = OUT / "_raw60.mp4"
    silent = OUT / "GeneHus_Clinician_Demo_silent.mp4"
    subprocess.run(
        [
            ff, "-y", "-i", str(webm),
            "-vf", f"scale={RW}:{RH}:flags=lanczos",
            *h264_args(),
            "-an", str(raw),
        ],
        check=True, capture_output=True,
    )
    dur = media_duration(raw)
    print(f"raw video {dur:.2f}s")
    # Extend closing by cloning final frame to exact 60s (clean end hold)
    if dur >= TARGET_SEC:
        cmd = [
            ff, "-y", "-i", str(raw), "-t", f"{TARGET_SEC:.2f}",
            *h264_args(), "-an", str(silent),
        ]
    else:
        pad = TARGET_SEC - dur
        cmd = [
            ff, "-y", "-i", str(raw),
            "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
            "-t", f"{TARGET_SEC:.2f}",
            *h264_args(), "-an", str(silent),
        ]
    subprocess.run(cmd, check=True, capture_output=True)
    # Probe bitrate
    probe = subprocess.run([ff, "-i", str(silent)], capture_output=True, text=True)
    for line in probe.stderr.splitlines():
        if "bitrate:" in line or "Video:" in line:
            print(" ", line.strip())
    print(f"silent exact {media_duration(silent):.2f}s 4K")
    return silent


async def make_voice(out_mp3: Path) -> None:
    raw = OUT / "_vo_full.mp3"
    await edge_tts.Communicate(NARRATION, VOICE, rate=RATE, pitch=PITCH).save(str(raw))
    dur = media_duration(raw)
    print(f"voice raw {dur:.2f}s ({VOICE})")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    if dur > TARGET_SEC - 0.4:
        tempo = max(0.5, min(2.0, dur / (TARGET_SEC - 0.6)))
        af = f"atempo={tempo:.4f},apad=whole_dur={TARGET_SEC:.2f}"
    else:
        af = f"apad=whole_dur={TARGET_SEC:.2f}"
    subprocess.run(
        [
            ff, "-y", "-i", str(raw), "-af", af, "-t", f"{TARGET_SEC:.2f}",
            "-ar", "44100", "-ac", "1", str(out_mp3),
        ],
        check=True, capture_output=True,
    )
    print(f"voice exact {media_duration(out_mp3):.2f}s")


def mux(silent: Path, audio: Path, out: Path) -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ff, "-y", "-i", str(silent), "-i", str(audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
            "-t", f"{TARGET_SEC:.2f}", "-movflags", "+faststart", str(out),
        ],
        check=True, capture_output=True,
    )
    print(f"final {out.name} {media_duration(out):.2f}s mb={out.stat().st_size/1e6:.2f}")


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
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo.mp4").write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(
            SCRIPT_MD, encoding="utf-8"
        )
        # cleanup local screenshots referenced by user
        for name in (
            "Screenshot 2026-08-22 062904.png",
            "Screenshot 2026-08-22 063250.png",
            "Screenshot 2026-08-22 063613.png",
        ):
            p = Path(r"c:\Users\fresh\Desktop\GeneHus") / name
            if p.exists():
                p.unlink()
                print("deleted", name)
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
