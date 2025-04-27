import os
from flask import Flask, request, Response, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import re

app = Flask(__name__)

def get_difficulty_value(driver):
    try:
        element = driver.find_element(By.CSS_SELECTOR, "[class*='parm-difficulty-']")
        match = re.search(r"parm-difficulty-(\d+)", element.get_attribute("class"))
        return match.group(1) if match else None
    except:
        return None

def get_animal_value(driver):
    try:
        element = driver.find_element(By.CSS_SELECTOR, "[class*='animal-']")
        cls = element.get_attribute("class")
        m = re.search(r"animal-(\d+)", cls)
        if not m: return None
        return "Bezpieczna dla zwierząt" if m.group(1)=="0" else "Szkodliwa dla zwierząt"
    except:
        return None

def get_scale_value(driver, selector):
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        m = re.search(r"scale-(\d+)", element.get_attribute("class"))
        return m.group(1) if m else None
    except:
        return None

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "Brak URL"}), 400

    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # nie musisz ustawiać binary_location, webdriver_manager to ogarnie
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME,"body")))

    # cena
    try:
        el = driver.find_element(By.CSS_SELECTOR, "span[itemprop='price']")
        price = el.text.strip() or el.get_attribute("content")
    except:
        price = None

    # obraz
    try:
        img = driver.find_element(By.CSS_SELECTOR, ".product-cover img")
        image_url = img.get_attribute("src")
    except:
        image_url = None

    # dodatkowe pola
    difficulty    = get_difficulty_value(driver)
    animal_status = get_animal_value(driver)
    air_cleaning  = get_scale_value(driver, ".parm-cleaning")
    sunlight      = get_scale_value(driver, ".parm-sun")
    watering      = get_scale_value(driver, ".parm-water")

    driver.quit()

    return Response(json.dumps({
        "url": url,
        "price": price,
        "image_url": image_url,
        "difficulty": difficulty,
        "animal_status": animal_status,
        "air_cleaning": air_cleaning,
        "sunlight": sunlight,
        "watering": watering
    }, ensure_ascii=False), mimetype="application/json")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
