"""
Tema Metal — LinkedIn Carousel Üretici
=====================================
Kullanım:
    python export/build_carousel.py           # tümü (shots + png + pdf)
    python export/build_carousel.py shots     # sadece sunumdan slayt görüntüleri
    python export/build_carousel.py pages     # carousel sayfalarını PNG + PDF olarak üret

Gereksinim: Google Chrome veya Microsoft Edge (headless modda kullanılır).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export"
OUT = EXPORT / "linkedin"
SHOTS = OUT / "shots"
PAGES = OUT / "pages"
CAROUSEL_HTML = EXPORT / "carousel.html"
PDF_PATH = OUT / "Tema_Metal_LinkedIn_Carousel.pdf"

# Carousel'de kullanılan sunum slaytları (kapak, izometrik akış, kapanış).
# Saha / dijital ikiz / kokpit sayfaları daha okunaklı olması için
# images/ klasöründeki orijinal yüksek çözünürlüklü görselleri kullanır.
# (çıktı adı, slayt id, ek URL parametresi, genişlik, yükseklik)
SLIDES = [
    ("s0", "s0", "", 1920, 1080),
    ("s2", "s2", "&freeze=12", 1920, 1080),   # akış 12. saniyede: 4 kollu üretim
    ("s7", "s7", "", 1920, 1080),
]
PAGE_COUNT = 9

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    sys.exit("Chrome / Edge bulunamadı.")


def file_url(path: Path, query: str = "", hash_: str = "") -> str:
    url = "file:///" + quote(path.as_posix(), safe="/:")
    if query:
        url += "?" + query
    if hash_:
        url += "#" + hash_
    return url


def run_browser(args, budget_ms: int):
    (EXPORT / ".chrome_profile").mkdir(exist_ok=True)
    profile = tempfile.mkdtemp(prefix="p_", dir=EXPORT / ".chrome_profile")
    cmd = [
        browser(),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        "--force-device-scale-factor=1",
        f"--user-data-dir={profile}",
        f"--virtual-time-budget={budget_ms}",
        *args,
    ]
    subprocess.run(cmd, check=True, timeout=180,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def shots(only=None):
    SHOTS.mkdir(parents=True, exist_ok=True)
    index = ROOT / "index.html"
    for name, sid, extra, w, h in SLIDES:
        if only and name not in only:
            continue
        out = SHOTS / f"{name}.png"
        run_browser([
            f"--window-size={w},{h}",
            f"--screenshot={out}",
            file_url(index, "export=1" + extra, sid),
        ], 8000)
        print(f"  ✓ {out.relative_to(ROOT)}")


def pages(only=None):
    PAGES.mkdir(parents=True, exist_ok=True)
    for i in range(1, PAGE_COUNT + 1):
        if only and str(i) not in only and f"sayfa_{i:02d}" not in only:
            continue
        out = PAGES / f"sayfa_{i:02d}.png"
        run_browser([
            "--window-size=1080,1350",
            f"--screenshot={out}",
            file_url(CAROUSEL_HTML, f"page={i}"),
        ], 3000)
        print(f"  ✓ {out.relative_to(ROOT)}")

    # 9 adet 1080x1350 PNG'yi doğrudan tek bir PDF'e birleştir
    imgs = [Image.open(PAGES / f"sayfa_{i:02d}.png").convert("RGB")
            for i in range(1, PAGE_COUNT + 1)]
    imgs[0].save(PDF_PATH, "PDF", resolution=144.0,
                 save_all=True, append_images=imgs[1:])
    shutil.rmtree(EXPORT / ".chrome_profile", ignore_errors=True)
    print(f"  ✓ {PDF_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = sys.argv[2:] or None
    if step in ("all", "shots"):
        print("Sunum slaytları yakalanıyor...")
        shots(only)
    if step in ("all", "pages"):
        print("Carousel sayfaları üretiliyor...")
        pages(only)
