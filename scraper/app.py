import os
import re
import json
from flask import Flask, request, Response, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
# Propagacja wyjątków wyłączona w prodzie
# app.config["PROPAGATE_EXCEPTIONS"] = True
# Debug wyłączony
app.config["DEBUG"] = False

# —————— Health-check endpoint ——————
@app.route('/', methods=['GET'])
def healthz():
    return 'OK', 200
# ————————————————————————————————

def get_difficulty_value(driver):
    try:
        el = driver.find_element(By.CSS_SELECTOR, "[class*='parm-difficulty-']")
        m = re.search(r"parm-difficulty-(\d+)", el.get_attribute("class"))
        return m.group(1) if m else None
    except:
        return None

def get_animal_value(driver):
    try:
        el = driver.find_element(By.CSS_SELECTOR, "[class*='animal-']")
        cls = el.get_attribute("class")
        m = re.search(r"animal-(\d+)", cls)
        if not m:
            return None
        return "Bezpieczna dla zwierząt" if m.group(1) == "0" else "Szkodliwa dla zwierząt"
    except:
        return None

def get_scale_value(driver, selector):
    try:
        el = driver.find_element(By.CSS_SELECTOR, selector)
        m = re.search(r"scale-(\d+)", el.get_attribute("class"))
        return m.group(1) if m else None
    except:
        return None

def get_short_description(driver):
    for sel in ("div.desktop-description-short p", "div.mobile-description-short p"):
        try:
            p = driver.find_element(By.CSS_SELECTOR, sel)
            text = p.text.strip()
            if text:
                return text
        except:
            pass
    return None

def get_care_instructions(driver):
    elems = driver.find_elements(By.CSS_SELECTOR, "div.product-description h3")
    for h3 in elems:
        if "Pielęgnacja" in h3.text:
            try:
                p = h3.find_element(By.XPATH, "following-sibling::p[1]")
                return p.text.strip()
            except:
                pass
    return None

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "Brak URL"}), 400

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    try:
        title_el = driver.find_element(By.CSS_SELECTOR, "h1.product-title, h1[itemprop='name'], h1")
        title = title_el.text.strip()
    except:
        title = None

    short_description = get_short_description(driver)
    care_instructions = get_care_instructions(driver)

    price = None
    for sel in (
        "span[itemprop='price']",
        ".current-price span",
        "span.price",
        "meta[property='product:price:amount']"
    ):
        if price:
            break
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            price = (el.get_attribute("content") or el.text).strip()
        except:
            continue

    try:
        img = driver.find_element(By.CSS_SELECTOR, ".product-cover img, img.main-image")
        image_url = img.get_attribute("src")
    except:
        image_url = None

    difficulty       = get_difficulty_value(driver)
    animal_status    = get_animal_value(driver)
    air_cleaning     = get_scale_value(driver, ".parm-cleaning")
    sunlight         = get_scale_value(driver, ".parm-sun")
    watering         = get_scale_value(driver, ".parm-water")

    driver.quit()

    result = {
        "url": url,
        "title": title,
        "short_description": short_description,
        "care_instructions": care_instructions,
        "price": price,
        "image_url": image_url,
        "difficulty": difficulty,
        "animal_status": animal_status,
        "air_cleaning": air_cleaning,
        "sunlight": sunlight,
        "watering": watering,
    }

    return Response(
        json.dumps(result, ensure_ascii=False, indent=2),
        mimetype="application/json"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    # W prodzie uruchamiaj przez Gunicorna, a nie flask run:
    #   gunicorn app:app --bind 0.0.0.0:$PORT
    app.run(host='0.0.0.0', port=port)
