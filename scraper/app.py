import os
import re
import time
import shutil
import logging
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ——— Configure logging ——————————————————————————————————————————
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def locate_chrome_binary():
    # 1) Try environment variable
    env = os.environ.get("CHROME_BIN")
    if env and shutil.which(env):
        return env
    # 2) Common binary names
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        path = shutil.which(name)
        if path:
            return path
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

@app.route('/', methods=['GET'])
def healthz():
    return 'OK', 200

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    logger.debug(f"🔎 scrape() start, url = {url}")
    if not url:
        logger.error("No URL provided")
        return jsonify({"success": False, "error": "Brak URL"}), 200

    # Locate Chrome/Chromium
    try:
        chrome_bin = locate_chrome_binary()
        logger.debug(f"Found Chrome binary: {chrome_bin}")
    except Exception as e:
        logger.error(f"Chrome binary error: {e}")
        return jsonify({"success": False, "error": str(e)}), 200

    # Create a unique profile directory
    timestamp = int(time.time() * 1000)
    profile_dir = f"/tmp/selenium_{os.getpid()}_{timestamp}"
    os.makedirs(profile_dir, exist_ok=True)
    logger.debug(f"Profile dir: {profile_dir}")

    # Chrome options
    options = webdriver.ChromeOptions()
    options.binary_location = chrome_bin
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--remote-debugging-port=0")

    service = Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        logger.debug("WebDriver started")
        driver.get(url)
        logger.debug("Page loaded, waiting for body")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract price
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

        # Extract image URL
        image_url = None
        try:
            img = driver.find_element(By.CSS_SELECTOR, ".product-cover img, img.main-image")
            image_url = img.get_attribute("src")
        except:
            pass

        # Extract other parameters
        difficulty    = get_difficulty_value(driver)
        animal_status = get_animal_value(driver)
        air_cleaning  = get_scale_value(driver, ".parm-cleaning")
        sunlight      = get_scale_value(driver, ".parm-sun")
        watering      = get_scale_value(driver, ".parm-water")

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
        logger.debug(f"Scrape success: {result}")
        return jsonify(result), 200

    except Exception as e:
        logger.exception("Exception during scrape")
        return jsonify({"success": False, "error": str(e)}), 200

    finally:
        logger.debug("Cleaning up WebDriver")
        if driver:
            try:
                driver.quit()
                logger.debug("WebDriver quit")
            except:
                pass
        try:
            shutil.rmtree(profile_dir)
            logger.debug("Profile dir removed")
        except:
            pass

# Use Gunicorn with:
#   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 1 --log-level debug --capture-output
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)), threaded=False)
