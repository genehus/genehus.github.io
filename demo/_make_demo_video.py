"""
GeneHus clinician-demo application video (full-length, H.264).
Fixes truncation by holding scenes longer, flushing the recorder, and
re-encoding with a real ffmpeg binary (imageio-ffmpeg).
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
from PIL import Image, ImageDraw, ImageOps
from playwright.sync_api import sync_playwright

ROOT = Path(r"c:\Users\fresh\Desktop\GeneHus\genehus.github.io")
OUT_DIR = ROOT / "demo" / "video"
WORK = OUT_DIR / "_work"
PORT = 8877
W, H = 1600, 900


def serve() -> socketserver.TCPServer:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # noqa: ANN002
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def make_poster() -> Path:
    """16:9 poster from genehuslogo — contain, not crop."""
    src = ROOT / "assets" / "genehuslogo.png"
    out = OUT_DIR / "poster.png"
    im = Image.open(src).convert("RGBA")
    canvas = Image.new("RGB", (W, H), (17, 17, 17))
    fitted = ImageOps.contain(im, (W - 160, H - 160))
    x = (W - fitted.width) // 2
    y = (H - fitted.height) // 2
    canvas.paste(fitted, (x, y), fitted if fitted.mode == "RGBA" else None)
    canvas.save(out, "PNG")
    # also overwrite site poster asset used by <video poster>
    site_poster = ROOT / "assets" / "genehuslogo-poster.png"
    canvas.save(site_poster, "PNG")
    print("poster", out, site_poster)
    return out


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
                  .wrap{{height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:40px 56px;box-sizing:border-box;background:radial-gradient(ellipse at 50% 20%,#2c3439 0%,#111 70%)}}
                  .eyebrow{{font-size:14px;letter-spacing:.18em;text-transform:uppercase;color:#f88820;font-weight:700;margin-bottom:16px}}
                  h1{{font-family:Oswald,sans-serif;font-weight:600;font-size:48px;letter-spacing:.04em;text-transform:uppercase;margin:0 0 16px;line-height:1.15;max-width:1000px}}
                  p{{font-size:20px;color:#d8dee4;max-width:820px;line-height:1.45;margin:0}}
                  .fine{{margin-top:24px;font-size:13px;color:#999;letter-spacing:.04em;text-transform:uppercase}}
                  .logo-frame{{width:min(880px,88vw);background:#ececec;padding:18px 22px;margin-bottom:22px;box-sizing:border-box}}
                  .logo-frame img{{display:block;width:100%;height:auto;max-height:340px;object-fit:contain}}
                </style></head><body><div class="wrap">{html}</div></body></html>""",
                wait_until="networkidle",
            )
            page.wait_for_timeout(int(seconds * 1000))

        logo = f"{base}/assets/genehuslogo.png"
        logo_block = (
            f'<div class="logo-frame"><img src="{logo}" alt="GeneHus"></div>'
        )

        card(
            logo_block
            + '<div class="eyebrow">Product demo · Application package</div>'
            "<h1>GeneHus clinician preview</h1>"
            "<p>African-trained genomic + clinical risk stratification for aggressive prostate cancer.</p>"
            '<div class="fine">Sample data only · Not for clinical use · Not Ghana FDA approved</div>',
            5.5,
        )
        card(
            '<div class="eyebrow">The problem</div>'
            "<h1>PSA alone misses who needs attention first</h1>"
            "<p>African men face among the highest prostate-cancer mortality and often present late. Hospitals still triage on PSA and clinical judgement.</p>"
            '<div class="fine">Ghana beachhead · Korle Bu / KATH pathway</div>',
            6.0,
        )
        card(
            '<div class="eyebrow">The product</div>'
            "<h1>A ranked hospital list for the clinician</h1>"
            "<p>GeneHus combines routine clinical inputs with an African genomic signal so the doctor can see who to review first — and stays in the loop.</p>"
            '<div class="fine">Hospital or lab sequences · GeneHus analyses</div>',
            6.0,
        )

        page.goto(f"{base}/demo/", wait_until="networkidle")
        page.wait_for_timeout(4500)

        page.click("#enter-btn")
        page.wait_for_url("**/demo/app.html")
        page.wait_for_selector("#queue-list .queue-item")
        page.wait_for_timeout(5000)  # Kwame high-risk overview

        for case_id, hold in (("benjamin", 5.5), ("ibrahim", 5.5), ("emmanuel", 5.0)):
            btn = page.locator(f'[data-id="{case_id}"]')
            btn.click()
            page.wait_for_timeout(int(hold * 1000))

        page.locator("#queue-list .queue-item").first.click()
        page.wait_for_timeout(4500)

        page.click("#new-case-btn")
        page.wait_for_timeout(2500)
        page.fill('input[name="age"]', "64")
        page.fill('input[name="psa"]', "18")
        page.select_option('select[name="gleason"]', "8")
        page.select_option('select[name="stage"]', "T2")
        page.uncheck('input[name="family"]')
        page.check('input[name="genomic"]')
        page.wait_for_timeout(1500)
        page.click('button[type="submit"]')
        page.wait_for_timeout(5500)

        card(
            '<div class="eyebrow">Honest status</div>'
            "<h1>Preview only — working v1 is not built yet</h1>"
            "<p>No real patients. No MADCaP data in this screen. Not validated. Not for clinical use. Nearest milestone: MADCaP permission, then v1, then hospital check versus PSA-alone.</p>"
            '<div class="fine">Interactive demo · genehus.bio/demo</div>',
            6.5,
        )
        card(
            logo_block
            + '<div class="eyebrow">GeneHus · Kumasi, Ghana</div>'
            "<h1>genehus.bio/demo</h1>"
            "<p>Try the clinician preview · safoduker@genehus.bio</p>"
            '<div class="fine">FAS Biocamp 2026 · Pre-seed application package</div>',
            6.5,
        )

        # Let the recorder flush the final seconds before teardown
        page.wait_for_timeout(1500)
        page.close()
        context.close()
        browser.close()

    videos = sorted(WORK.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise SystemExit("No Playwright video recorded")
    return videos[0]


def webm_to_mp4(webm: Path) -> Path:
    out = OUT_DIR / "GeneHus_Clinician_Demo.mp4"
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
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
        "-movflags",
        "+faststart",
        "-an",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(ROOT)
    make_poster()
    httpd = serve()
    time.sleep(0.5)
    try:
        webm = record_demo()
        print("recorded", webm, "mb", round(webm.stat().st_size / 1e6, 2))
        dest_webm = OUT_DIR / "GeneHus_Clinician_Demo.webm"
        shutil.copy2(webm, dest_webm)
        mp4 = webm_to_mp4(webm)
        print("wrote", mp4, "mb", round(mp4.stat().st_size / 1e6, 2))
        print("wrote", dest_webm)
    finally:
        httpd.shutdown()
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
