import os
import re
import json
import shutil
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def locate_chrome_binary():
    # 1) Spróbuj ENV
    env_path = os.environ.get("CHROME_BIN")
    if env_path and shutil.which(env_path):
        return env_path
    # 2) Typowe nazwy
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    raise RuntimeError(
        "Nie znaleziono Chrome/Chromium. "
        "Ustaw ENV CHROME_BIN lub zainstaluj chromium."
    )

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
        return "Bezpieczna dla zwierząt" if m.group(1)=="0" else "Szkodliwa dla zwierząt"
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
    url  = data.get("url")
    if not url:
        return jsonify({"success": False, "error": "Brak URL"}), 200

    # 1) Znajdź binarkę
    try:
        chrome_bin = locate_chrome_binary()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200

    # 2) Ustawcie opcje Chrome
    options = webdriver.ChromeOptions()
    options.binary_location = chrome_bin
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    # Kluczowa flaga, żeby za każdym razem użyć wolnego portu DevTools:
    options.add_argument("--remote-debugging-port=0")

    service = Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    driver  = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # --- price ---
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

        return jsonify({
            "success": True,
            "url": url,
            "price": price,
            "image_url": image_url,
            "difficulty": difficulty,
            "animal_status": animal_status,
            "air_cleaning": air_cleaning,
            "sunlight": sunlight,
            "watering": watering,
        }), 200

    except Exception as e:
        # zawsze zwróć success:false, nie HTTP 500
        return jsonify({"success": False, "error": str(e)}), 200

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# W Render.com użyj gunicorn: 
#   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 1
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",3000)), threaded=False)
