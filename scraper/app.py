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
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["DEBUG"] = True

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
        m = re.search(r"animal-(\d+)", el.get_attribute("class"))
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
    """
    Szuka krótkiego opisu w desktop i mobile view:
    <div class="desktop-description-short"><p>…</p></div>
    <div class="mobile-description-short"><p>…</p></div>
    """
    for sel in (".desktop-description-short p", ".mobile-description-short p"):
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            txt = el.text.strip()
            if txt:
                return txt
        except:
            pass
    return None

def get_care_instructions(driver):
    """
    Znajduje nagłówek H3 zawierający słowo "Pielęgnacja"
    i zwraca tekst pierwszego <p> po nim.
    """
    try:
        xpath = "//h3[contains(normalize-space(.), 'Pielęgnacja')]/following-sibling::p[1]"
        el = driver.find_element(By.XPATH, xpath)
        return el.text.strip()
    except:
        return None

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "Brak URL"}), 400

    # uruchamiamy headless Chrome
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=opts)
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # krótki opis
    short_description  = get_short_description(driver)
    # instrukcje pielęgnacji
    care_instructions  = get_care_instructions(driver)

    # ———- wyciąganie ceny ———-
    price = None
    try:
        el = driver.find_element(By.CSS_SELECTOR, "span[itemprop='price']")
        price = el.get_attribute("content") or el.text.strip()
    except:
        pass

    if not price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, "span.price")
            price = el.text.strip()
        except:
            pass

    if not price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".current-price span")
            price = el.get_attribute("content") or el.text.strip()
        except:
            pass

    if not price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, "meta[property='product:price:amount']")
            price = el.get_attribute("content")
        except:
            pass

    # obraz
    try:
        img = driver.find_element(By.CSS_SELECTOR, ".product-cover img")
        image_url = img.get_attribute("src")
    except:
        image_url = None

    # inne atrybuty
    difficulty      = get_difficulty_value(driver)
    animal_status   = get_animal_value(driver)
    air_cleaning    = get_scale_value(driver, ".parm-cleaning")
    sunlight        = get_scale_value(driver, ".parm-sun")
    watering        = get_scale_value(driver, ".parm-water")

    driver.quit()

    out = {
        "url":               url,
        "short_description": short_description,
        "care_instructions": care_instructions,
        "price":             price,
        "image_url":         image_url,
        "difficulty":        difficulty,
        "animal_status":     animal_status,
        "air_cleaning":      air_cleaning,
        "sunlight":          sunlight,
        "watering":          watering,
    }

    return Response(
        json.dumps(out, ensure_ascii=False, indent=2),
        mimetype="application/json"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
