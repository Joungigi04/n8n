import os
import re
import logging
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

# — Logging ——————————————————————————————————————————
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def extract_price(soup):
    for sel in (
        "span[itemprop='price']",
        ".current-price span",
        "span.price",
        "meta[property='product:price:amount']"
    ):
        tag = soup.select_one(sel)
        if tag:
            val = tag.get("content") or tag.get_text()
            if val:
                return val.strip()
    return None

def extract_image(soup):
    # only the img inside .rc_ratio_list
    el = soup.select_one(".rc_ratio_list img")
    if not el:
        return None
    # check the correct attribute names
    for attr in ("data-original", "data-src", "src"):
        url = el.get(attr)
        if url:
            return url.strip()
    return None

def extract_scale(soup, base_class):
    """
    base_class e.g. 'parm-cleaning', 'parm-sun', 'parm-water'
    Returns the number from either '<base_class>-X' or 'scale-X' in its classes.
    """
    el = soup.select_one(f".{base_class}")
    if not el:
        return None
    for cls in el.get("class", []):
        # direct prefix match: parm-cleaning-1 etc.
        m = re.match(rf"{re.escape(base_class)}-(\d+)", cls)
        if m:
            return m.group(1)
        # or the scale form: scale-2 etc.
        m2 = re.match(r"scale-(\d+)", cls)
        if m2:
            return m2.group(1)
    return None

@app.route('/', methods=['GET'])
def healthz():
    return "OK", 200

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url", "").strip()
    if not url:
        return jsonify(success=False, error="Brak URL"), 200
    logger.debug(f"🔎 scrape() start, url={url}")

    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        return jsonify(success=False, error=f"Fetch failed: {e}"), 200

    # Now extract everything
    price         = extract_price(soup)
    image_url     = extract_image(soup)
    difficulty    = extract_scale(soup, "parm-difficulty")

    animal_status = None
    animal_el = soup.select_one("[class*='animal-']")
    if animal_el:
        for cls in animal_el.get("class", []):
            m = re.match(r"animal-(\d+)", cls)
            if m:
                animal_status = (
                    "Bezpieczna dla zwierząt" if m.group(1) == "0"
                    else "Szkodliwa dla zwierząt"
                )
                break

    air_cleaning  = extract_scale(soup, "parm-cleaning")
    sunlight      = extract_scale(soup, "parm-sun")
    watering      = extract_scale(soup, "parm-water")

    result = {
        "success":       True,
        "url":           url,
        "price":         price,
        "image_url":     image_url,
        "difficulty":    difficulty,
        "animal_status": animal_status,
        "air_cleaning":  air_cleaning,
        "sunlight":      sunlight,
        "watering":      watering,
    }
    logger.debug(f"Scrape result: {result}")
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), threaded=False)

