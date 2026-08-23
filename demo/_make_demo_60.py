"""
GeneHus clinician demo — 70.00s (silent)
- ~12s open cards · ~52.5s hospital screen · ~5s close (same ratios as prior 60s/90s cuts)
- Opening logo: transparent white (website style)
- Closing logo: GeneHus_Logo_ (white-on-transparent)
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
PORT = 8882
# Capture at full-bleed 1080p (record size MUST match viewport — larger = gray corner bug),
# then lanczos-upscale to true 4K UHD so the player fills edge-to-edge.
VW, VH = 1920, 1080
RW, RH = 3840, 2160
POSTER_W, POSTER_H = 1920, 1080
TARGET_SEC = 70.0

SCRIPT_MD = """# GeneHus Clinician Demo — silent (no voiceover)

**Length:** exactly 70.00 seconds · 4K · no audio track  
**Pacing:** ~12s open · ~52.5s hospital screen · ~5s close (scaled from the prior 60s proportions)
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
            device_scale_factor=1,
            record_video_dir=str(WORK),
            # Must equal viewport. Playwright paints CSS pixels into this canvas;
            # if larger (e.g. 4K with 1080p viewport), content sits top-left on gray.
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
            2.3,
        )
        card(
            '<div class="eyebrow">The problem</div>'
            "<h1>PSA alone misses who needs attention first</h1>"
            "<p>African men face among the highest prostate-cancer mortality and often present late.</p>"
            '<div class="fine">Ghana beachhead · tertiary hospitals</div>',
            2.3,
        )
        card(
            '<div class="eyebrow">The product</div>'
            "<h1>A ranked hospital list for the clinician</h1>"
            "<p>Combine clinical inputs with an African genomic signal. The doctor stays in the loop.</p>"
            '<div class="fine">Hospital or lab sequences · GeneHus analyses</div>',
            2.1,
        )

        # Enter app — ~52.5s on hospital screen (75% of 70s)
        page.goto(f"{base}/demo/app.html", wait_until="domcontentloaded")
        page.wait_for_selector("#queue-list .queue-item")
        page.wait_for_timeout(300)

        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(19000)

        page.locator('[data-id="benjamin"]').click()
        page.wait_for_timeout(11500)
        page.locator('[data-id="ibrahim"]').click()
        page.wait_for_timeout(11500)
        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(10500)

        # ~5s close
        card(
            f'<div class="logo-plain logo-end">'
            f'<img src="{end_logo}" alt="GeneHus" '
            f'style="width:min(1180px,70vw);height:auto;max-height:260px;object-fit:contain;display:block">'
            f"</div>"
            '<div class="eyebrow">GeneHus · Kumasi, Ghana</div>'
            "<h1>genehus.bio/demo</h1>"
            "<p>Try the clinician preview</p>",
            4.3,
            wrap_class="wrap-end",
        )

        page.wait_for_timeout(200)
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
    """Constant quantizer 4K — keeps detail on UI screens (bitrate mode under-fills static slides)."""
    return [
        "-c:v", "libx264",
        "-preset", "medium",
        "-qp", "16",
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
            "-vf", f"scale={RW}:{RH}:flags=lanczos,setsar=1",
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
        final = OUT / "GeneHus_Clinician_Demo.mp4"
        shutil.copy2(silent, final)
        print(f"final {final.name} {media_duration(final):.2f}s mb={final.stat().st_size/1e6:.2f} (silent)")
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo.mp4").write_bytes(final.read_bytes())
        Path(r"c:\Users\fresh\Desktop\GeneHus\GeneHus_Clinician_Demo_VOICEOVER_SCRIPT.md").write_text(
            SCRIPT_MD, encoding="utf-8"
        )
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
