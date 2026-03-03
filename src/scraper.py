import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from selenium.webdriver.common.by import By
from urllib3.util.retry import Retry

from src.models import Product
from src.utils.selenium_utils import get_driver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/allinone/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/computers/laptops/")

USER_AGENT = UserAgent()
BASE_HEADERS = {
    "User-Agent": USER_AGENT.random,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def build_headers() -> dict[str, str]:
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = USER_AGENT.random
    return headers


def create_session() -> requests.Session:
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    http_session = requests.Session()
    http_session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    http_session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    return http_session


SESSION = create_session()


def close_session() -> None:
    SESSION.close()


def get_home_products() -> list[Product]:
    try:
        response = SESSION.get(
            HOME_URL,
            headers=build_headers(),
            timeout=10,
            verify=True,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features="html.parser")
        products = soup.select(".card-body")
        return [parse_single_product(product) for product in products]
    except requests.exceptions.RequestException as error:
        logging.error(f"Помилка при виконанні запиту до HOME_URL: {error}")
        return []
    except Exception as error:
        logging.warning(f"Неочікувана помилка в get_home_products(): {error}")
        return []


def parse_single_product(product: Tag) -> Product:
    hdd_prices = parse_hdd_block_prices(product)
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
        additional_info={"hdd_prices": hdd_prices},
    )


def get_laptop_page_products() -> list[Product]:
    try:
        response = SESSION.get(
            LAPTOP_URL,
            headers=build_headers(),
            timeout=10,
            verify=True,
        )
        response.raise_for_status()
        first_page_soup = BeautifulSoup(response.content, features="html.parser")
        all_products = get_single_page_products(first_page_soup)
        num_pages = get_num_pages(first_page_soup)

        logging.info(f"Всього знайдено сторінок: {num_pages}")
        logging.info(f"Початок парсингу сторінки 1 з {num_pages}")

        for page_num in range(2, num_pages + 1):
            logging.info(f"Початок парсингу сторінки {page_num} з {num_pages}")
            response = SESSION.get(
                LAPTOP_URL,
                headers=build_headers(),
                params={"page": page_num},
                timeout=10,
                verify=True,
            )
            response.raise_for_status()
            next_page_soup = BeautifulSoup(response.content, features="html.parser")
            all_products.extend(get_single_page_products(next_page_soup))

        logging.info(f"Всього знайдено товарів: {len(all_products)}")
        return all_products
    except requests.exceptions.RequestException as error:
        logging.error(f"Помилка при завантаженні сторінок: {error}")
        return []
    except Exception as error:
        logging.warning(f"Неочікувана помилка: {error}")
        return []


def get_num_pages(page_soup: Tag) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    try:
        absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
        driver = get_driver()
        driver.get(absolute_url)

        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")
        prices: dict[str, float] = {}

        for button in buttons:
            if button.get_property("disabled"):
                continue
            button.click()
            price_text = driver.find_element(By.CLASS_NAME, "price").text
            price_value = float(price_text.replace("$", ""))
            config_name = button.get_property("value")
            prices[config_name] = price_value
            logging.info(f"HDD конфігурація '{config_name}' -> ${price_value}")

        return prices
    except Exception as error:
        logging.warning(f"Помилка при парсингу HDD блоків: {error}")
        return {}

