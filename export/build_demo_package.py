"""
Tema Metal — Canlı Demo Yayın Paketi Üretici
============================================
1) LinkedIn / WhatsApp link önizlemesi için images/og_cover.jpg (1200x630) üretir.
2) Sunumun web yayınına hazır, görselleri optimize edilmiş kopyasını
   export/demo_site/ klasörüne ve export/linkedin/Tema_Metal_Canli_Demo.zip
   dosyasına çıkarır (Netlify Drop / GitHub Pages için sürükle-bırak hazır).
"""
import shutil
import zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export"
DEMO = EXPORT / "demo_site"
ZIP_PATH = EXPORT / "linkedin" / "Tema_Metal_Canli_Demo.zip"

SITE_FILES = [
    "index.html",
    "izometrik_akis.html",
    "style.css",
    "script.js",
]


def make_og_cover():
    src = EXPORT / "linkedin" / "shots" / "s0.png"
    if not src.exists():
        return
    im = Image.open(src).convert("RGB").resize((1200, 675), Image.LANCZOS)
    # 1200x630 (Open Graph standardı)
    im = im.crop((0, 22, 1200, 652))
    out = ROOT / "images" / "og_cover.jpg"
    im.save(out, "JPEG", quality=88, optimize=True)
    print(f"  ✓ {out.relative_to(ROOT)}")


def copy_and_optimize_images(src_dir: Path, dst_dir: Path, max_w: int):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.iterdir():
        if not p.is_file():
            continue
        dst = dst_dir / p.name
        ext = p.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            im = Image.open(p).convert("RGB")
            if im.width > max_w:
                h = int(im.height * (max_w / im.width))
                im = im.resize((max_w, h), Image.LANCZOS)
            im.save(dst, "JPEG", quality=82, optimize=True)
        elif ext == ".png":
            im = Image.open(p)
            if im.width > max_w:
                h = int(im.height * (max_w / im.width))
                im = im.resize((max_w, h), Image.LANCZOS)
            # Dashboard ekran görüntüleri opak: P-mode / optimize PNG ile ciddi küçülür
            if im.mode in ("RGB", "RGBA") and "logo" not in p.name.lower() and src_dir.name == "images":
                im_q = im.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)
                im_q.save(dst, "PNG", optimize=True)
            else:
                im.save(dst, "PNG", optimize=True)
        else:
            shutil.copy2(p, dst)


def build_demo():
    make_og_cover()
    if DEMO.exists():
        shutil.rmtree(DEMO)
    DEMO.mkdir(parents=True)

    for f in SITE_FILES:
        shutil.copy2(ROOT / f, DEMO / f)

    copy_and_optimize_images(ROOT / "images", DEMO / "images", max_w=1920)
    copy_and_optimize_images(ROOT / "assets" / "flow", DEMO / "assets" / "flow", max_w=900)

    # Zip paketi
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in DEMO.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(DEMO))

    orig_mb = sum(p.stat().st_size for p in [*(ROOT / "images").glob("*"), *(ROOT / "assets" / "flow").glob("*")] if p.is_file()) / (1024 * 1024)
    demo_mb = sum(p.stat().st_size for p in DEMO.rglob("*") if p.is_file()) / (1024 * 1024)
    zip_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"  ✓ Görsel boyutu: {orig_mb:.1f} MB -> {demo_mb:.1f} MB (demo klasörü)")
    print(f"  ✓ {ZIP_PATH.relative_to(ROOT)} ({zip_mb:.2f} MB)")


if __name__ == "__main__":
    build_demo()

