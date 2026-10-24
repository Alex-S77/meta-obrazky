"""Render Meta catalog images (design C, "vstupenka") for Futbalový sen.

Reads the product feed from the web (the Mergado input, original photos), draws a 1080x1080 ticket-style card per match from
the match photo and feed data, and writes the site for GitHub Pages:

  site/img/<id>-<hash>.jpg   one image per match; the hash changes with the
                             content, so Meta re-downloads changed images
  site/images.csv            g:id;g:image_link for the Mergado data import

Usage: python generate.py FEED_URL OUT_DIR BASE_URL
       python generate.py --sample OUT_DIR   (offline preview from sample.xml)
"""
import csv, hashlib, io, os, re, sys, time, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1080
# Brand palette (design manual): gradient #e26427 -> #e6313a, red #e52e10
OR, RD, RD2, BK, GREY = (226, 100, 39), (230, 49, 58), (229, 46, 16), (14, 14, 16), (130, 130, 140)
WHITE = (255, 255, 255)
UA = {"User-Agent": "futbalovysen-meta-images/1.0"}


def font(weight, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", f"Inter-{weight}.otf"), size)


LOGO = Image.open(os.path.join(HERE, "assets", "logo-biele.png")).convert("RGBA")


# ---------- feed ----------

def parse_feed(xml_bytes):
    """Return one dict per <item>, keys without XML namespace (g:title -> title)."""
    root = ET.fromstring(xml_bytes)
    items = []
    for el in root.iter():
        if el.tag.split("}")[-1] not in ("item", "entry"):
            continue
        d = {}
        for ch in el:
            k = ch.tag.split("}")[-1]
            d.setdefault(k, (ch.text or "").strip())
        if d.get("id"):
            items.append(d)
    return items


def match_texts(p):
    parts = [s.strip() for s in p.get("title", "").split("|")]
    title = parts[0].replace(" - ", " – ")
    tag = " · ".join(parts[1:]) or p.get("sutaz", "")
    return title, tag


def fmt_price(raw):
    m = re.search(r"[\d.,]+", raw or "")
    if not m:
        return ""
    val = float(m.group().replace(",", "."))
    whole = f"{round(val):,}".replace(",", " ")
    return f"{whole} €"


# ---------- drawing helpers ----------

def lin_grad(w, h, c0, c1, angle):
    xs, ys = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    t = xs * np.cos(angle) + ys * np.sin(angle)
    t = (t - t.min()) / (t.max() - t.min())
    out = np.stack([c0[i] + (c1[i] - c0[i]) * t for i in range(3)], -1)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def grain(im, amt, rng):
    a = np.asarray(im).astype(np.int16)
    n = rng.normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def cover(photo, w, h, fy=0.4):
    sc = max(w / photo.width, h / photo.height)
    im = photo.resize((round(photo.width * sc), round(photo.height * sc)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def fit(d, text, weight, size, min_size, max_w):
    """Largest font size <= size at which text fits max_w (one line)."""
    while size > min_size and d.textlength(text, font=font(weight, size)) > max_w:
        size -= 2
    return font(weight, size)


def wrap2(d, text, weight, size, max_w):
    """Split text into two lines at the space closest to the middle."""
    words = text.split(" ")
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wid = max(d.textlength(a, font=font(weight, size)), d.textlength(b, font=font(weight, size)))
        if best is None or wid < best[0]:
            best = (wid, a, b)
    return best


def tri(d, pts, width=5, filled=False):
    if filled:
        d.polygon(pts, fill=WHITE)
    else:
        d.line(pts + [pts[0]], fill=WHITE, width=width, joint="curve")


# ---------- design C ----------

def render(p, photo):
    rng = np.random.default_rng(int(hashlib.md5(p["id"].encode()).hexdigest()[:8], 16))
    im = grain(lin_grad(S, S, OR, RD, 0.8), 24, rng)
    d = ImageDraw.Draw(im)
    tri(d, [(700, 30), (1060, 150), (900, 260)])
    tri(d, [(-40, 900), (160, 1060), (-20, 1100)])
    tri(d, [(960, 60), (1030, 110), (975, 150)], filled=True)
    lw = 250
    lg = LOGO.resize((lw, round(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
    im.paste(lg, (64, 52), lg)

    x0, y0, x1, y1 = 60, 175, S - 60, 1020
    card = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((0, 0, card.width, card.height), radius=30, fill=WHITE)
    pw, ph = card.width - 40, 470
    if photo is not None:
        pic = cover(photo, pw, ph)
    else:
        pic = lin_grad(pw, ph, (40, 40, 48), BK, 0.5)
    pm = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(pm).rounded_rectangle((0, 0, pw, ph), radius=20, fill=255)
    card.paste(pic, (20, 20), pm)

    sy = 650
    for cx in (0, card.width):
        cd.ellipse((cx - 26, sy - 26, cx + 26, sy + 26), fill=(0, 0, 0, 0))
    for x in range(50, card.width - 40, 28):
        cd.line([(x, sy), (x + 14, sy)], fill=(210, 210, 215), width=3)

    title, tag = match_texts(p)
    max_w = card.width - 80
    f = fit(cd, title, "Black", 50, 38, max_w)
    if cd.textlength(title, font=f) <= max_w:
        cd.text((40, 515), title, font=f, fill=BK)
        tag_y = 580
    else:
        _, a, b = wrap2(cd, title, "Black", 38, max_w)
        f = fit(cd, max(a, b, key=len), "Black", 38, 28, max_w)
        cd.text((40, 500), a, font=f, fill=BK)
        cd.text((40, 545), b, font=f, fill=BK)
        tag_y = 597
    cd.text((40, tag_y), tag, font=fit(cd, tag, "SemiBold", 30, 22, max_w), fill=RD2)

    cd.text((40, 690), "DÁTUM", font=font("Bold", 22), fill=GREY)
    cd.text((40, 720), p.get("datum_zapasu_sk", ""), font=font("Bold", 38), fill=BK)
    stadium = p.get("stadion", "")
    cd.text((330, 690), "ŠTADIÓN" if stadium else "MIESTO", font=font("Bold", 22), fill=GREY)
    place = stadium or p.get("mesto", "")
    cd.text((330, 720), place, font=fit(cd, place, "Bold", 38, 22, 270), fill=BK)

    pg = lin_grad(320, 120, OR, RD, 0.3)
    pmask = Image.new("L", (320, 120), 0)
    ImageDraw.Draw(pmask).polygon([(28, 0), (320, 0), (292, 120), (0, 120)], fill=255)
    card.paste(pg, (card.width - 350, 680), pmask)
    cd.text((card.width - 190, 712), "už od", font=font("Medium", 26), fill=WHITE, anchor="mm")
    price = fmt_price(p.get("price") or p.get("sale_price"))
    cd.text((card.width - 190, 762), price, font=fit(cd, price, "Black", 46, 30, 250), fill=WHITE, anchor="mm")

    im = im.convert("RGBA")
    im.alpha_composite(card, (x0, y0))
    return im.convert("RGB")


# ---------- pipeline ----------

def fetch_photo(url, cache):
    # never re-render our own output (the Meta feed carries it after the import)
    if not url or "github.io" in url:
        return None
    if url in cache:
        return cache[url]
    try:
        r = requests.get(url, headers=UA, timeout=30)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:  # unreadable format (e.g. .avif) or download error
        print(f"photo failed: {url}: {e}", file=sys.stderr)
        img = None
    cache[url] = img
    return img


def content_hash(p):
    keys = ("title", "price", "sale_price", "datum_zapasu_sk", "stadion", "image_link")
    raw = "|".join(p.get(k, "") for k in keys) + "|v1"
    return hashlib.sha1(raw.encode()).hexdigest()[:10]


def build(items, out_dir, base_url, photos):
    os.makedirs(os.path.join(out_dir, "img"), exist_ok=True)
    rows = []
    for p in items:
        name = f"{re.sub(r'[^A-Za-z0-9_-]', '_', p['id'])}-{content_hash(p)}.jpg"
        render(p, photos.get(p.get("image_link"))).save(
            os.path.join(out_dir, "img", name), "JPEG", quality=87, optimize=True)
        rows.append((p["id"], f"{base_url.rstrip('/')}/img/{name}"))
    with open(os.path.join(out_dir, "images.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["g:id", "g:image_link"])
        w.writerows(rows)
    # contact sheet of the first 12 images for a quick visual check
    sheet = Image.new("RGB", (4 * 360, 3 * 360), WHITE)
    for i, (_, url) in enumerate(rows[:12]):
        tile = Image.open(os.path.join(out_dir, "img", url.rsplit("/", 1)[1])).resize((360, 360))
        sheet.paste(tile, ((i % 4) * 360, (i // 4) * 360))
    sheet.save(os.path.join(out_dir, "nahlad.jpg"), quality=85)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><meta charset=utf-8><title>Futbalový sen – Meta obrázky</title>"
                 f"<p>{len(rows)} obrázkov. <a href='images.csv'>images.csv</a></p>"
                 "<img src='nahlad.jpg' style='max-width:100%'>")
    print(f"rendered {len(rows)} images")


def is_sk(items):
    foreign = [p for p in items if "futbalovysen.sk" not in p.get("link", "")]
    return bool(items) and len(foreign) <= len(items) // 10


def fetch_sk_feed(feed_url, tries=8, wait=45):
    """The web's feed cache flips between the SK and the CZ feed (fotbalovysen.cz,
    other ids); CZ items match nothing in Mergado. Bust the cache and retry until
    the SK one comes back, otherwise give up so the last good deploy stays."""
    for i in range(tries):
        sep = "&" if "?" in feed_url else "?"
        r = requests.get(f"{feed_url}{sep}nocache={int(time.time())}{i}", headers=UA, timeout=120)
        r.raise_for_status()
        items = parse_feed(r.content)
        if is_sk(items):
            print(f"SK feed on try {i + 1}: {len(items)} items")
            return items, r.content
        print(f"try {i + 1}: not the SK feed ({len(items)} items)", file=sys.stderr)
        time.sleep(wait)
    return None, None


def main():
    if sys.argv[1] == "--sample":
        out = sys.argv[2]
        items = parse_feed(open(os.path.join(HERE, "sample.xml"), "rb").read())
        sample_photo = os.path.join(HERE, "assets", "sample-photo.png")
        photos = {p.get("image_link"): Image.open(sample_photo).convert("RGB") for p in items}
        build(items, out, "https://example.invalid", photos)
        return
    feed_url, out, base_url = sys.argv[1:4]
    items, raw = fetch_sk_feed(feed_url)
    if items is None:
        # not an error worth a failure e-mail every hour: skip, the last deploy stays
        print("feed is not the SK one, keeping the last deploy")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                fh.write("skip=true\n")
        return
    cache = {}
    urls = sorted({p.get("image_link", "") for p in items})
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda u: fetch_photo(u, cache), urls))
    build(items, out, base_url, cache)
    # verified SK copy of the feed, Mergado's SK projects import this instead of the web
    with open(os.path.join(out, "feed-sk.xml"), "wb") as fh:
        fh.write(raw)


if __name__ == "__main__":
    main()
