import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

def scrape_product(url: str) -> dict:
    """
    Headless Chromium + Selenium – odczytujemy produkt z Tomaszewski.pl.
    """
    # Konfiguracja headless Chromium
    options = Options()
    # Jeżeli w Twoim Alpine Chromium jest pod inną ścieżką, dostosuj to:
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(5)

        # Tytuł produktu: PrestaShop używa itemprop="name"
        try:
            title_el = driver.find_element(By.CSS_SELECTOR, "[itemprop='name']")
            title = title_el.text.strip()
        except NoSuchElementException:
            title = None

        # Cena: PrestaShop używa itemprop="price"
        try:
            price_el = driver.find_element(By.CSS_SELECTOR, "[itemprop='price']")
            # cena może być w atrybucie content lub w tekście
            price = price_el.get_attribute("content") or price_el.text.strip()
        except NoSuchElementException:
            price = None

        return {
            "url": url,
            "title": title,
            "price": price,
        }
    finally:
        driver.quit()


if __name__ == "__main__":
    # do lokalnego testu
    import json
    result = scrape_product("https://tomaszewski.pl/begonia-kingiana-2")
    print(json.dumps(result, ensure_ascii=False, indent=2))
