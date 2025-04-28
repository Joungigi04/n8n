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

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "Brak URL"}), 400

    # --- konfiguracja przeglądarki ---
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    # --- otwieramy stronę i czekamy aż się załaduje ---
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # --- tytuł produktu ---
    try:
        title_el = driver.find_element(By.CSS_SELECTOR, "h1.product-title, h1[itemprop='name'], h1")
        title = title_el.text.strip()
    except:
        title = None

    # --- cena ---
    price = None
    # 1) span[itemprop=price]
    try:
        el = driver.find_element(By.CSS_SELECTOR, "span[itemprop='price']")
        price = el.get_attribute("content") or el.text.strip()
    except:
        pass

    # 2) fallback .current-price span
    if not price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".current-price span")
            price = el.get_attribute("content") or el.text.strip()
        except:
            pass

    # 3) fallback span.price
    if not price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, "span.price")
            price = el.text.strip()
        except:
            pass

    # 4) meta[property=product:price:amount]
    if not price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, "meta[property='product:price:amount']")
            price = el.get_attribute("content")
        except:
            pass

    # --- obrazek ---
    try:
        img = driver.find_element(By.CSS_SELECTOR, ".product-cover img, img.main-image")
        image_url = img.get_attribute("src")
    except:
        image_url = None

    # --- pozostałe atrybuty ---
    difficulty    = get_difficulty_value(driver)
    animal_status = get_animal_value(driver)
    air_cleaning  = get_scale_value(driver, ".parm-cleaning")
    sunlight      = get_scale_value(driver, ".parm-sun")
    watering      = get_scale_value(driver, ".parm-water")

    driver.quit()

    result = {
        "url": url,
        "title": title,
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
    app.run(host='0.0.0.0', port=port, debug=True)

