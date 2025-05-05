import os
import re
import json
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.config["DEBUG"] = False

# Health-check endpoint
@app.route('/', methods=['GET'])
def healthz():
    return 'OK', 200

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

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"success": False, "error": "Brak URL"}), 200

    # Chrome in headless mode, disable sandbox + disable-dev-shm, enable remote debugging
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")              # wyłącza GPU, czasem konieczne na headless
    options.add_argument("--single-process")           # wymusza pojedynczy proces renderowania
    options.add_argument("--disable-extensions")       # wyłącza rozszerzenia
    options.add_argument("--window-size=1920,1080")    # niektóre strony potrzebują nadać wymiary

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # --- price extraction ---
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

        # --- image ---
        try:
            img = driver.find_element(By.CSS_SELECTOR, ".product-cover img, img.main-image")
            image_url = img.get_attribute("src")
        except:
            image_url = None

        difficulty    = get_difficulty_value(driver)
        animal_status = get_animal_value(driver)
        air_cleaning  = get_scale_value(driver, ".parm-cleaning")
        sunlight      = get_scale_value(driver, ".parm-sun")
        watering      = get_scale_value(driver, ".parm-water")

        result = {
            "success": True,
            "url": url,
            "price": price,
            "image_url": image_url,
            "difficulty": difficulty,
            "animal_status": animal_status,
            "air_cleaning": air_cleaning,
            "sunlight": sunlight,
            "watering": watering,
        }
        return jsonify(result), 200

    except Exception as e:
        # Catch everything, return JSON instead of HTTP 500
        return jsonify({"success": False, "error": str(e)}), 200

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    # In production launch via gunicorn:
    # gunicorn app:app --bind 0.0.0.0:$PORT
    app.run(host='0.0.0.0', port=port)
