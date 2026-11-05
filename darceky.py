"""Meta catalog images for Futbalové darčeky (futbalovedarceky.sk).

Two styles, switched by the env var DARCEKY_STYLE:
  C (default) "karta": light background, product photo on a white card,
                       price in a navy circle, green band in the logo colours
  A           "vianoce": dark navy with snow and a green glow, product cut out
                         from its white background, price on a lime tag

Products come from two feeds, joined on g:id:
  DARCEKY_IDS_FEED    Mergado output feed of the Meta project: which products
                      are exported (its image_link is already ours, so only ids)
  DARCEKY_PHOTO_FEED  the shop's own feed (Mergado input): original photos,
                      titles, prices

Output: OUT_DIR/darceky/img/<id>-<hash>.jpg and OUT_DIR/darceky/images.csv
(g:id;g:image_link) for the Mergado data import. Photos are cached in
PHOTO_CACHE so each run only downloads new or changed photos.

Usage: python darceky.py OUT_DIR BASE_URL
       python darceky.py --sample OUT_DIR [A|C]   (offline, uses assets/sample-photo.png)
"""
import csv, hashlib, io, os, random, re, sys, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1080
LIME, GREEN, NAVY, DARK = (160, 198, 19), (8, 153, 94), (29, 36, 51), (14, 19, 32)
UA = {"User-Agent": "futbalovedarceky-meta-images/1.0"}
LOGO = Image.open(os.path.join(HERE, "assets", "darceky-logo.png")).convert("RGBA")
VERSION = "v1"


def font(weight, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", f"Inter-{weight}.otf"), size)


# ---------- feeds ----------

def parse_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = {}
    for el in root.iter():
        if el.tag.split("}")[-1] not in ("item", "entry"):
            continue
        d = {}
        for ch in el:
            d.setdefault(ch.tag.split("}")[-1], (ch.text or "").strip())
        if d.get("id"):
            items[d["id"]] = d
    return items


def get(url):
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    return r.content


def price_text(raw):
    m = re.search(r"\d+(?:[.,]\d+)?", raw or "")
    if not m:
        return ""
    return f"{float(m.group().replace(',', '.')):.2f}".replace(".", ",")


# ---------- drawing helpers ----------

def logo(w):
    return LOGO.resize((w, round(LOGO.height * w / LOGO.width)), Image.LANCZOS)


def vgrad(size, c1, c2, horizontal=False):
    w, h = size
    t = np.linspace(0, 1, w if horizontal else h)
    row = np.stack([c1[i] + (c2[i] - c1[i]) * t for i in range(3)], -1).astype(np.uint8)
    arr = np.broadcast_to(row[None, :, :], (h, w, 3)) if horizontal else np.broadcast_to(row[:, None, :], (h, w, 3))
    return Image.fromarray(np.ascontiguousarray(arr), "RGB")


def glow(size, center, radius, color, alpha):
    m = Image.new("L", size, 0)
    x, y = center
    ImageDraw.Draw(m).ellipse((x - radius, y - radius * 0.75, x + radius, y + radius * 0.75), fill=alpha)
    lay = Image.new("RGBA", size, color + (0,))
    lay.putalpha(m.filter(ImageFilter.GaussianBlur(radius * 0.45)))
    return lay


def wrap(d, text, f, maxw, lines=2):
    out = [""]
    for word in text.split():
        t = (out[-1] + " " + word).strip()
        if d.textlength(t, font=f) <= maxw:
            out[-1] = t
        else:
            out.append(word)
    if len(out) > lines:
        out = out[:lines]
        while d.textlength(out[-1] + "…", font=f) > maxw and " " in out[-1]:
            out[-1] = out[-1].rsplit(" ", 1)[0]
        out[-1] += "…"
    return out


def fit_into(im, maxw, maxh):
    r = min(maxw / im.width, maxh / im.height)
    return im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)


def trim_white(photo):
    """Crop the white margin around the product."""
    a = np.asarray(photo.convert("RGB")).astype(np.int16)
    ys, xs = np.where((a < 235).any(-1))
    if len(xs) == 0:
        return photo
    return photo.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def cutout(photo):
    """Make the white background (white areas touching the border) transparent."""
    rgb = photo.convert("RGB")
    a = np.asarray(rgb).astype(np.int16)
    white = (a > 236).all(-1)
    lab, _ = ndimage.label(white)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0])
    alpha = Image.fromarray(np.where(bg, 0, 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out.crop(alpha.getbbox() or (0, 0, out.width, out.height))


def chip_for(p):
    t = (p.get("title", "") + " " + p.get("description", "")).lower()
    return "Potlač mena a čísla" if "potla" in t else ""


# ---------- style C (karta) ----------

def render_c(p, photo):
    im = Image.new("RGBA", (W, W), (243, 246, 236, 255))
    band = vgrad((W, W), LIME, GREEN, horizontal=True).convert("RGBA")
    m = Image.new("L", (W, W), 0)
    ImageDraw.Draw(m).polygon([(0, 700), (W, 520), (W, W), (0, W)], fill=255)
    band.putalpha(m)
    im.alpha_composite(band)
    sh = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((90, 150, 990, 830), radius=44, fill=(0, 0, 0, 70))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)), (0, 14))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 150, 990, 830), radius=44, fill="white")
    L = logo(400)
    im.alpha_composite(L, (90, 40))
    if photo is not None:
        pr = fit_into(trim_white(photo).convert("RGBA"), 760, 600)
        im.alpha_composite(pr, ((W - pr.width) // 2, 190 + (600 - pr.height) // 2))
    price, sale = price_text(p.get("price")), price_text(p.get("sale_price"))
    cx, cy, r = 900, 180, 118
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=NAVY)
    shown = sale or price
    if shown:
        f = font("Black", 54 if len(shown) <= 5 else 46)
        d.text((cx, cy - 8), shown, font=f, fill="white", anchor="mm")
        d.text((cx, cy + 42), "EUR", font=font("Bold", 26), fill=LIME, anchor="mm")
    if sale and price and sale != price:
        tag = f"Zľava z {price} €"
        f2 = font("Bold", 24)
        tw = d.textlength(tag, font=f2)
        d.rounded_rectangle((cx - tw / 2 - 18, cy + r - 6, cx + tw / 2 + 18, cy + r + 40), radius=23, fill=LIME)
        d.text((cx, cy + r + 17), tag, font=f2, fill=DARK, anchor="mm")
    f = font("Black", 42)
    y0 = 868
    for ln in wrap(d, p.get("title", ""), f, 900):
        d.text((90, y0), ln, font=f, fill="white")
        y0 += 52
    chip = chip_for(p)
    if chip:
        f3 = font("Bold", 26)
        tw = d.textlength(chip, font=f3)
        d.rounded_rectangle((90, y0 + 12, 90 + tw + 48, y0 + 64), radius=26, fill="white")
        d.text((114, y0 + 38), chip, font=f3, fill=GREEN, anchor="lm")
    return im.convert("RGB")


# ---------- style A (vianoce) ----------

def render_a(p, photo):
    im = vgrad((W, W), (26, 36, 58), DARK).convert("RGBA")
    im.alpha_composite(glow((W, W), (540, 470), 430, GREEN, 150))
    snow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(snow)
    rnd = random.Random(7)
    for _ in range(170):
        x, y = rnd.randrange(W), rnd.randrange(W)
        r = rnd.choice([1.5, 2, 2.5, 3, 4])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.randrange(60, 200)))
    im.alpha_composite(snow.filter(ImageFilter.GaussianBlur(0.6)))
    L = logo(380)
    im.alpha_composite(L, ((W - L.width) // 2, 52))
    if photo is not None:
        pr = fit_into(cutout(photo), 760, 590)
        x, y = (W - pr.width) // 2, 170 + (590 - pr.height) // 2
        sh = Image.new("RGBA", (pr.width + 120, pr.height + 120), (0, 0, 0, 0))
        sh.paste(Image.new("RGBA", pr.size, (0, 0, 0, 110)), (60, 60), pr.split()[3])
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)), (x - 60, y - 42))
        im.alpha_composite(pr, (x, y))
    d = ImageDraw.Draw(im)
    d.text((70, 815), "DARČEK POD STROMČEK", font=font("Bold", 28), fill=LIME)
    f = font("Black", 44)
    y0 = 860
    for ln in wrap(d, p.get("title", ""), f, 600):
        d.text((70, y0), ln, font=f, fill="white")
        y0 += 56
    shown = price_text(p.get("sale_price")) or price_text(p.get("price"))
    if shown:
        txt = f"{shown} €"
        fp = font("Black", 58)
        tw = d.textlength(txt, font=fp)
        d.rounded_rectangle((W - 70 - tw - 64, 858, W - 70, 958), radius=50, fill=LIME)
        d.text((W - 70 - tw / 2 - 32, 908), txt, font=fp, fill=DARK, anchor="mm")
    return im.convert("RGB")


STYLES = {"A": render_a, "C": render_c}


# ---------- pipeline ----------

def photo_path(cache_dir, url):
    return os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".img")


def fetch_photo(url, cache_dir):
    if not url or "github.io" in url:
        return
    path = photo_path(cache_dir, url)
    if os.path.exists(path):
        return
    try:
        data = get(url)
        Image.open(io.BytesIO(data)).verify()
        with open(path, "wb") as fh:
            fh.write(data)
    except Exception as e:
        print(f"photo failed: {url}: {e}", file=sys.stderr)


def load_photo(url, cache_dir):
    path = photo_path(cache_dir, url or "")
    if not url or not os.path.exists(path):
        return None
    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


def content_hash(p, style):
    keys = ("title", "price", "sale_price", "image_link", "description")
    raw = "|".join(p.get(k, "") for k in keys) + f"|{style}|{VERSION}"
    return hashlib.sha1(raw.encode()).hexdigest()[:10]


def build(products, out_dir, base_url, cache_dir, style):
    render = STYLES[style]
    img_dir = os.path.join(out_dir, "darceky", "img")
    os.makedirs(img_dir, exist_ok=True)
    rows, ok = [], 0
    for p in products:
        photo = load_photo(p.get("image_link"), cache_dir)
        if photo is None:
            continue  # no photo: leave the product's own image in the feed
        name = f"{re.sub(r'[^A-Za-z0-9_-]', '_', p['id'])}-{content_hash(p, style)}.jpg"
        render(p, photo).save(os.path.join(img_dir, name), "JPEG", quality=88, optimize=True)
        rows.append((p["id"], f"{base_url.rstrip('/')}/darceky/img/{name}"))
        ok += 1
    with open(os.path.join(out_dir, "darceky", "images.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["g:id", "g:image_link"])
        w.writerows(rows)
    sheet = Image.new("RGB", (4 * 360, 3 * 360), "white")
    for i, (_, url) in enumerate(rows[:12]):
        tile = Image.open(os.path.join(img_dir, url.rsplit("/", 1)[1])).resize((360, 360))
        sheet.paste(tile, ((i % 4) * 360, (i // 4) * 360))
    sheet.save(os.path.join(out_dir, "darceky", "nahlad.jpg"), quality=85)
    print(f"darceky: rendered {ok} of {len(products)} products (style {style})")
    return ok


def main():
    if sys.argv[1] == "--sample":
        out, style = sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "C")
        cache = os.path.join(out, "_cache")
        os.makedirs(cache, exist_ok=True)
        src = os.path.join(HERE, "assets", "sample-photo.png")
        url = "file://sample"
        with open(photo_path(cache, url), "wb") as fh:
            fh.write(open(src, "rb").read())
        items = [{"id": "SAMPLE1", "title": "Detský dres Yamal FC Barcelona 2026/27 domáci replika",
                  "price": "27.90 EUR", "image_link": url},
                 {"id": "SAMPLE2", "title": "Sada Slovensko pre deti a dospelých s potlačou",
                  "price": "34.90 EUR", "sale_price": "29.90 EUR", "image_link": url}]
        build(items, out, "https://example.invalid", cache, style)
        return
    out, base_url = sys.argv[1:3]
    style = os.environ.get("DARCEKY_STYLE", "C").strip().upper() or "C"
    cache_dir = os.environ.get("PHOTO_CACHE", "photo-cache")
    os.makedirs(cache_dir, exist_ok=True)
    ids = parse_feed(get(os.environ["DARCEKY_IDS_FEED"]))
    shop = parse_feed(get(os.environ["DARCEKY_PHOTO_FEED"]))
    products = [shop[i] for i in ids if i in shop]
    print(f"darceky: {len(ids)} exported ids, {len(products)} found in the shop feed")
    if len(products) < max(50, len(ids) // 2):
        raise SystemExit("darceky: too few products matched, keeping the last deploy")
    urls = sorted({p.get("image_link", "") for p in products})
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda u: fetch_photo(u, cache_dir), urls))
    if build(products, out, base_url, cache_dir, style) < len(products) // 2:
        raise SystemExit("darceky: too few images rendered, keeping the last deploy")


if __name__ == "__main__":
    main()
