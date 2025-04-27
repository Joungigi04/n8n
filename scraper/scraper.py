from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def scrape_product(url: str) -> dict:
    """
    Otwiera stronę pod podanym URL-em w headless Chrome,
    odczytuje tytuł i cenę produktu (CSS-selectory dostosuj do swojej strony)
    i zwraca słownik z wynikami.
    """
    # konfiguracja headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        # poczekaj chwilę, jeśli strona ładuje się dynamicznie
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

        # (opcjonalnie) inne pola, np. opis, SKU, obraz:
        # img_el = driver.find_element("css selector", "img.main-image")
        # img_url = img_el.get_attribute("src")

        return {
            "url": url,
            "title": title,
            "price": price,
            # "imageUrl": img_url,
        }
    finally:
        driver.quit()
