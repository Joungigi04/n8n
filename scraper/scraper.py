from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def scrape_product(url: str) -> dict:
    """
    Otwiera stronę pod podanym URL-em w headless Chromium,
    odczytuje tytuł i cenę produktu i zwraca słownik z wynikami.
    """

    # konfiguracja headless Chromium
    options = Options()
    # tutaj wskazujemy lokalizację binarki Chromium w kontenerze
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        driver.implicitly_wait(5)

        # odczyt tytułu
        try:
            title_el = driver.find_element("css selector", "h1.product-title")
            title = title_el.text.strip()
        except NoSuchElementException:
            title = None

        # odczyt ceny
        try:
            price_el = driver.find_element("css selector", "span.price")
            price = price_el.text.strip()
        except NoSuchElementException:
            price = None

        return {
            "url": url,
            "title": title,
            "price": price,
        }

    finally:
        driver.quit()
