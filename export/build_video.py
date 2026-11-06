"""
Tema Metal — LinkedIn Video Üretici (1080x1350, 4:5 dikey, 24 fps)
==================================================================
Akış (~36 sn):
  0.0 –  2.0 sn : Kapak (sayfa_01.png)
  2.0 – 23.0 sn : Canlı İzometrik Üretim Akışı (0 -> 28 sn tam döngü)
 23.0 – 30.0 sn : 3D Fabrika Dijital İkizi + Canlı WhatsApp Arıza Bildirimi
 30.0 – 33.0 sn : Stratejik Kazanımlar (sayfa_08.png)
 33.0 – 36.0 sn : Kapanış & Çağrı (sayfa_09.png)
"""
import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote

import aiohttp
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export"
OUT = EXPORT / "linkedin"
PAGES = OUT / "pages"
STAGE_HTML = EXPORT / "video_stage.html"
VIDEO_PATH = OUT / "Tema_Metal_LinkedIn_Video.mp4"

W, H = 1080, 1350
FPS = 24

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    raise RuntimeError("Chrome / Edge bulunamadı.")


def file_url(path: Path) -> str:
    return "file:///" + quote(path.as_posix(), safe="/:")


def blend(a: np.ndarray, b: np.ndarray, alpha: float) -> np.ndarray:
    return cv2.addWeighted(a, 1.0 - alpha, b, alpha, 0)


async def cdp_call(ws, msg_id: int, method: str, params: dict | None = None):
    await ws.send_json({"id": msg_id, "method": method, "params": params or {}})
    while True:
        msg = await ws.receive_json()
        if msg.get("id") == msg_id:
            return msg.get("result", {})


async def capture_stage_frames():
    (EXPORT / ".chrome_profile").mkdir(exist_ok=True)
    profile = tempfile.mkdtemp(prefix="v_", dir=EXPORT / ".chrome_profile")
    port = 9333
    proc = subprocess.Popen([
        find_browser(),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        "--force-device-scale-factor=1",
        f"--window-size={W},{H}",
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={port}",
        file_url(STAGE_HTML),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # CDP hazır olana kadar bekle
        targets = None
        for _ in range(40):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1) as r:
                    targets = json.loads(r.read().decode())
                if targets:
                    break
            except Exception:
                time.sleep(0.25)
        page_ws = next(t["webSocketDebuggerUrl"] for t in targets if t.get("type") == "page")

        flow_frames: list[np.ndarray] = []
        twin_frames: list[np.ndarray] = []

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(page_ws, max_msg_size=64 * 1024 * 1024) as ws:
                mid = 1
                await cdp_call(ws, mid, "Page.enable"); mid += 1
                await cdp_call(ws, mid, "Emulation.setDeviceMetricsOverride", {
                    "width": W, "height": H, "deviceScaleFactor": 1, "mobile": False,
                }); mid += 1

                # Fontların ve iframe'in yüklenmesi için kısa bekleme
                await asyncio.sleep(2.5)
                # Kamerayı başlangıç noktasına oturtmak için birkaç ısınma adımı
                for _ in range(15):
                    await cdp_call(ws, mid, "Runtime.evaluate", {
                        "expression": "window.renderStage('flow', 0, 0)",
                    }); mid += 1

                # 1) İZOMETRİK AKIŞ: 21 sn (504 kare) boyunca 0 -> 28 sn
                n_flow = 21 * FPS
                print(f"İzometrik akış yakalanıyor ({n_flow} kare)...")
                for i in range(n_flow):
                    sim_t = (i / (n_flow - 1)) * 27.6
                    prog = 0.06 + 0.58 * (i / n_flow)
                    await cdp_call(ws, mid, "Runtime.evaluate", {
                        "expression": f"window.renderStage('flow', {sim_t:.4f}, {prog:.4f})",
                    }); mid += 1
                    res = await cdp_call(ws, mid, "Page.captureScreenshot", {
                        "format": "jpeg", "quality": 94,
                    }); mid += 1
                    raw = base64.b64decode(res["data"])
                    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                    flow_frames.append(img)
                    if (i + 1) % 96 == 0 or i == n_flow - 1:
                        print(f"  · akış {i + 1}/{n_flow}")

                # 2) 3D DİJİTAL İKİZ: 7 sn (168 kare)
                n_twin = 7 * FPS
                print(f"3D Dijital İkiz yakalanıyor ({n_twin} kare)...")
                for i in range(n_twin):
                    sec = i / FPS
                    prog = 0.64 + 0.20 * (i / n_twin)
                    await cdp_call(ws, mid, "Runtime.evaluate", {
                        "expression": f"window.renderStage('twin', {sec:.4f}, {prog:.4f})",
                    }); mid += 1
                    res = await cdp_call(ws, mid, "Page.captureScreenshot", {
                        "format": "jpeg", "quality": 94,
                    }); mid += 1
                    raw = base64.b64decode(res["data"])
                    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                    twin_frames.append(img)

        return flow_frames, twin_frames
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(EXPORT / ".chrome_profile", ignore_errors=True)


def read_img(path: Path) -> np.ndarray:
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def build():
    cover = read_img(PAGES / "sayfa_01.png")
    results = read_img(PAGES / "sayfa_08.png")
    cta = read_img(PAGES / "sayfa_09.png")

    flow_frames, twin_frames = asyncio.run(capture_stage_frames())

    # OpenCV Windows'ta ASCII olmayan tam yollarda sorun çıkarabildiği için göreli yol kullan
    rel_video = str(VIDEO_PATH.relative_to(Path.cwd()))
    writer = cv2.VideoWriter(
        rel_video,
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (W, H),
    )

    n_fade = 10  # ~0.4 sn yumuşak geçiş

    # Bölüm 1: Kapak (2 sn) -> Akışa geçiş
    for i in range(int(1.8 * FPS)):
        writer.write(cover)
    for i in range(n_fade):
        writer.write(blend(cover, flow_frames[0], (i + 1) / n_fade))

    # Bölüm 2: Canlı İzometrik Akış (21 sn)
    for fr in flow_frames:
        writer.write(fr)

    # Geçiş: Akış -> Dijital İkiz
    for i in range(n_fade):
        writer.write(blend(flow_frames[-1], twin_frames[0], (i + 1) / n_fade))

    # Bölüm 3: 3D Dijital İkiz & WhatsApp (7 sn)
    for fr in twin_frames:
        writer.write(fr)

    # Geçiş: Dijital İkiz -> Sonuçlar (3 sn)
    for i in range(n_fade):
        writer.write(blend(twin_frames[-1], results, (i + 1) / n_fade))
    for _ in range(int(2.8 * FPS)):
        writer.write(results)

    # Geçiş: Sonuçlar -> Kapanış CTA (3 sn)
    for i in range(n_fade):
        writer.write(blend(results, cta, (i + 1) / n_fade))
    for _ in range(int(2.8 * FPS)):
        writer.write(cta)

    writer.release()
    mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"✓ Video hazır: {VIDEO_PATH.relative_to(ROOT)} ({mb:.2f} MB)")


if __name__ == "__main__":
    build()
