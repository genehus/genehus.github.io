"""
GeneHus clinician-demo application video
Produces: genehus.github.io/demo/video/GeneHus_Clinician_Demo.mp4
"""
from __future__ import annotations

import http.server
import shutil
import socketserver
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"c:\Users\fresh\Desktop\GeneHus\genehus.github.io")
OUT_DIR = ROOT / "demo" / "video"
FRAMES = OUT_DIR / "_work"
PORT = 8876


def serve() -> socketserver.TCPServer:
    handler = http.server.SimpleHTTPRequestHandler

    class Quiet(handler):
        def log_message(self, *args):  # noqa: ANN002
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def record_demo() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)

    base = f"http://127.0.0.1:{PORT}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            device_scale_factor=1.5,
            record_video_dir=str(FRAMES),
            record_video_size={"width": 1600, "height": 900},
        )
        page = context.new_page()

        # --- Title cards via data URLs (clean application open) ---
        def card(html: str, seconds: float) -> None:
            page.set_content(
                f"""<!DOCTYPE html><html><head><meta charset="utf-8">
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
                <style>
                  html,body{{margin:0;height:100%;background:#111;color:#fff;font-family:Lato,Helvetica,sans-serif}}
                  .wrap{{height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:48px;box-sizing:border-box;background:radial-gradient(ellipse at 50% 20%,#2c3439 0%,#111 70%)}}
                  .eyebrow{{font-size:14px;letter-spacing:.18em;text-transform:uppercase;color:#f88820;font-weight:700;margin-bottom:18px}}
                  h1{{font-family:Oswald,sans-serif;font-weight:600;font-size:56px;letter-spacing:.04em;text-transform:uppercase;margin:0 0 18px;line-height:1.1;max-width:980px}}
                  p{{font-size:22px;color:#d8dee4;max-width:780px;line-height:1.45;margin:0}}
                  .fine{{margin-top:28px;font-size:13px;color:#999;letter-spacing:.04em;text-transform:uppercase}}
                  img{{height:52px;margin-bottom:28px}}
                </style></head><body><div class="wrap">{html}</div></body></html>""",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(int(seconds * 1000))

        logo = f"{base}/assets/genehuslogo.png"
        card(
            f'<img src="{logo}" alt="GeneHus" style="height:auto;width:min(720px,86vw);margin-bottom:22px">'
            '<div class="eyebrow">Product demo · Application package</div>'
            "<h1>GeneHus clinician preview</h1>"
            "<p>African-trained genomic + clinical risk stratification for aggressive prostate cancer.</p>"
            '<div class="fine">Sample data only · Not for clinical use · Not Ghana FDA approved</div>',
            4.5,
        )
        card(
            '<div class="eyebrow">The problem</div>'
            "<h1>PSA alone misses who needs attention first</h1>"
            "<p>African men face among the highest prostate-cancer mortality and often present late. Hospitals still triage on PSA and clinical judgement.</p>"
            '<div class="fine">Ghana beachhead · Korle Bu / KATH pathway</div>',
            5.0,
        )
        card(
            '<div class="eyebrow">The product</div>'
            "<h1>A ranked hospital list for the clinician</h1>"
            "<p>GeneHus combines routine clinical inputs with an African genomic signal so the doctor can see who to review first — and stays in the loop.</p>"
            '<div class="fine">Hospital or lab sequences · GeneHus analyses</div>',
            5.0,
        )

        # --- Live demo gate ---
        page.goto(f"{base}/demo/", wait_until="networkidle")
        page.wait_for_timeout(3500)

        # Enter app
        page.click("#enter-btn")
        page.wait_for_url("**/demo/app.html")
        page.wait_for_selector("#queue-list .queue-item")
        page.wait_for_timeout(2500)

        # Highlight queue / first case (Kwame high)
        page.wait_for_timeout(3500)

        # Switch to a second case (Benjamin — modest PSA, genomic flag)
        btn = page.locator('[data-id="benjamin"]')
        if btn.count():
            btn.click()
            page.wait_for_timeout(4000)

        # Switch to Ibrahim (unclear PSA)
        btn = page.locator('[data-id="ibrahim"]')
        if btn.count():
            btn.click()
            page.wait_for_timeout(4000)

        # Back to highest risk
        first = page.locator("#queue-list .queue-item").first
        first.click()
        page.wait_for_timeout(3500)

        # New sample case flow
        page.click("#new-case-btn")
        page.wait_for_timeout(2000)
        page.fill('input[name="psa"]', "18")
        page.select_option('select[name="gleason"]', "8")
        page.check('input[name="genomic"]')
        page.click('button[type="submit"]')
        page.wait_for_timeout(4000)

        # Closing cards
        card(
            '<div class="eyebrow">Honest status</div>'
            "<h1>Preview only — working v1 is not built yet</h1>"
            "<p>No real patients. No MADCaP data in this screen. Not validated. Not for clinical use. Nearest milestone: MADCaP permission, then v1, then hospital check versus PSA-alone.</p>",
            5.5,
        )
        card(
            f'<img src="{logo}" alt="GeneHus" style="height:auto;width:min(720px,86vw);margin-bottom:22px">'
            '<div class="eyebrow">GeneHus · Kumasi, Ghana</div>'
            "<h1>genehus.bio/demo</h1>"
            "<p>Try the clinician preview · safoduker@genehus.bio</p>"
            '<div class="fine">FAS Biocamp 2026 · Pre-seed application package</div>',
            4.5,
        )

        page.close()
        context.close()
        browser.close()

    videos = list(FRAMES.glob("*.webm"))
    if not videos:
        raise SystemExit("No Playwright video recorded")
    return videos[0]


def webm_to_mp4(webm: Path) -> Path:
    """Convert with Playwright-bundled ffmpeg if present, else OpenCV."""
    out = OUT_DIR / "GeneHus_Clinician_Demo.mp4"
    ffmpeg_candidates = list(Path.home().joinpath("AppData/Local/ms-playwright").glob("ffmpeg-*/ffmpeg-win64/ffmpeg.exe"))
    if ffmpeg_candidates:
        import subprocess

        ff = ffmpeg_candidates[0]
        cmd = [
            str(ff),
            "-y",
            "-i",
            str(webm),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(out),
        ]
        subprocess.run(cmd, check=True)
        return out

    # Fallback: OpenCV re-encode (may drop some frames)
    import cv2

    cap = cv2.VideoCapture(str(webm))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        writer.write(frame)
    cap.release()
    writer.release()
    return out


def main() -> None:
    # Serve from site root so /demo and /assets resolve
    import os

    os.chdir(ROOT)
    httpd = serve()
    time.sleep(0.4)
    try:
        webm = record_demo()
        print("recorded", webm)
        mp4 = webm_to_mp4(webm)
        print("wrote", mp4, "size_mb", round(mp4.stat().st_size / 1e6, 2))
        # Keep a copy of webm too for browsers that prefer it
        dest_webm = OUT_DIR / "GeneHus_Clinician_Demo.webm"
        shutil.copy2(webm, dest_webm)
        print("wrote", dest_webm)
    finally:
        httpd.shutdown()
        if FRAMES.exists():
            shutil.rmtree(FRAMES, ignore_errors=True)


if __name__ == "__main__":
    main()
