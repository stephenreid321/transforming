"""Chapter opener artwork -> alpha masks (assets/hero/chapter-N.webp), plus the
social preview image (assets/og.jpg). Run after tools/art.py."""
import numpy as np
import pymupdf
from PIL import Image

INK = {1: "4f0e64", 2: "232176", 3: "004b1c", 4: "005e5a", 5: "5c5349", 6: "700044"}
OPENERS = {1: 13, 2: 33, 3: 50, 4: 69, 5: 88, 6: 106}
PDF = "Transforming how we lead together.pdf"

for n, page_no in OPENERS.items():
    page = pymupdf.open(PDF)[page_no - 1]
    page.add_redact_annot(page.rect)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                          text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    W, H = page.rect.width, page.rect.height
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=pymupdf.Rect(0, 0, W / 2, H))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(np.float32)
    ink = np.array([int(INK[n][i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
    q = (img[::8, ::8] // 8).reshape(-1, 3)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    # background = most common colour that is lighter than the ink
    order = np.argsort(-counts)
    bg = None
    for i in order:
        c = vals[i] * 8 + 4
        if c.sum() > ink.sum() + 150:
            bg = c
            break
    v = ink - bg
    a = np.clip(((img - bg) @ v) / float(v @ v), 0, 1)
    rgba = np.zeros(a.shape + (4,), dtype=np.uint8)
    rgba[:, :, 3] = (a * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(f"assets/hero/chapter-{n}.webp", quality=72, method=6)

cover = pymupdf.open(PDF)[0]
pix = cover.get_pixmap(matrix=pymupdf.Matrix(1200 / cover.rect.width, 1200 / cover.rect.width))
im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
og = Image.new("RGB", (1200, 630), im.getpixel((10, 10)))
og.paste(im.crop((0, 0, 1200, 630)), (0, 0))
og.save("assets/og.jpg", quality=85)
print("heroes + og done")
