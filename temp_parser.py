# Бібліотека для виконання HTTP-запитів (GET, POST тощо)
# Використовується для завантаження HTML-сторінок
import requests

# BeautifulSoup - бібліотека для парсингу HTML та XML
# Дозволяє зручно працювати з тегами, класами, атрибутами
from bs4 import BeautifulSoup, Tag

# urllib - вбудована бібліотека Python для роботи з URL-адресами
# Функція urljoin використовується для коректного об'єднання базового URL з відносними шляхами
# Захищає від помилок зі слешами ("/") при складанні адрес
from urllib.parse import urljoin

# fake_useragent - стороння бібліотека для генерації випадкових User-Agent
# Імітує запити від різних браузерів (Chrome, Firefox, Safari тощо)
# Допомагає зробити HTTP-запит схожим на запит від реального користувача
from fake_useragent import UserAgent

# urllib3 - стороння бібліотека для роботи з HTTP-запитами
# Retry - механізм повторних HTTP-запитів у разі помилок або збоїв з'єднання
# Дозволяє автоматично повторювати запити при тимчасових помилках сервера
# (наприклад 500, 502, 503, 504)
from urllib3.util.retry import Retry

# HTTPAdapter - дозволяє підключити механізм Retry до requests.Session
# Використовується для налаштування повторних запитів, таймаутів і адаптерів з'єднання
from requests.adapters import HTTPAdapter


# Імпортуємо декоратор dataclass для створення класів даних
# Дозволяє створювати класи, які:
# - зберігають дані у вигляді атрибутів
# - автоматично генерують методи __init__, __repr__, __eq__ та ін.
# - роблять код більш чистим та зручним для обробки структурованих даних
from dataclasses import dataclass, fields, astuple

# Модуль дозволяє читати та записувати дані в CSV файл
import csv

# Вбудований модуль для логування подій
import logging

# Модуль для роботи з системними функціями
import sys

# webdriver - основний модуль для керування браузером
# Дозволяє створювати екземпляр браузера (Chrome, Firefox тощо)
# та виконувати різні дії: навігація, кліки, отримання контенту
from selenium import webdriver

# By - клас для визначення стратегій пошуку елементів на сторінці
# Дозволяє шукати елементи за різними критеріями:
# - By.ID, By.CLASS_NAME, By.TAG_NAME, By.CSS_SELECTOR тощо
from selenium.webdriver.common.by import By

# Конфігуруємо систему логування
logging.basicConfig(
    # Рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    level=logging.INFO,
    # Формат виводу повідомлень:
    # [РІВЕНЬ]: Повідомлення
    format="[%(levelname)s]: %(message)s",
    # Обробники для виводу логів:
    handlers=[
        # Запис в файл parser.log з кодуванням UTF-8
        logging.FileHandler("parser.log", encoding="utf-8"),
        # Вивід логів в консоль (stdout)
        logging.StreamHandler(sys.stdout),
    ]
)



@dataclass
class Product:
    # Назва товару
    title: str
    # Детальний опис товару
    description: str
    # Ціна у вигляді числа з плаваючою точкою
    price: float
    # Рейтинг товару (ціле число від 1 до 5)
    rating: int
    # Кількість відгуків про товар
    num_of_reviews: int
    # Інформація про конфігурації товару та ціни на конфігурації
    # Словник формату: {"назва_конфігурації": ціна}
    additional_info: dict[str, float]

# Отримуємо імена всіх полів класу Product для використання в CSV-заголовку,
# що дозволить автоматично оновлювати заголовки, якщо ми змінимо модель даних
PRODUCT_FIELDS = [field.name for field in fields(Product)]

# Глобальна змінна для зберігання екземпляра WebDriver
# WebDriver | None - типізація: може бути WebDriver або None
_driver: webdriver.WebDriver | None = None


def get_driver() -> webdriver.WebDriver:
    """
    Повертає поточний екземпляр WebDriver

    Returns:
        webdriver.WebDriver: активний екземпляр браузера

    Raises:
        AttributeError: якщо драйвер не був ініціалізований
    """
    return _driver


def set_driver(new_driver: webdriver.WebDriver) -> None:
    """
    Встановлює новий екземпляр WebDriver як глобальний

    Args:
        new_driver: новий екземпляр WebDriver для використання
    """
    global _driver
    _driver = new_driver

# Створюємо об'єкт генератора випадкових User-Agent
# Кожен виклик user_agent.random повертає інший User-Agent браузера
user_agent = UserAgent()

# Налаштовуємо стратегію повторних HTTP-запитів
retry_strategy = Retry(
    total=3,  # Максимальна кількість спроб (1 основна + 2 повтори)
    backoff_factor=1,  # Базова затримка між спробами (секунди), зростає експоненційно (1s...2s...4s)
    status_forcelist=[  # Коди помилок, при яких треба повторювати запит
        429,  # Too Many Requests (занадто багато запитів, сервер тимчасово блокує)
        500,  # Internal Server Error (внутрішня помилка сервера)
        502,  # Bad Gateway (сервер отримав некоректну відповідь від іншого сервера)
        503,  # Service Unavailable (сервер тимчасово недоступний)
        504  # Gateway Timeout (сервер не отримав відповідь від іншого сервера)
    ],
    # Retry застосовується тільки до GET-запитів
    allowed_methods=["GET"]
)

# Створюємо HTTP-сесію
# Session дозволяє:
# - повторно використовувати TCP-з'єднання
# - виконувати запити швидше, ніж requests.get()
# - задавати глобальні налаштування (headers, retry тощо)
session = requests.Session()

# Підключаємо retry-стратегію для HTTPS-запитів
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

# Підключаємо retry-стратегію для HTTP-запитів
session.mount("http://", HTTPAdapter(max_retries=retry_strategy))

# Базовий домен сайту
BASE_URL = "https://webscraper.io/"

# Головна сторінка магазину
# urljoin поєднує базовий URL та відносний шлях,
# гарантуючи коректну адресу незалежно від слешів
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/allinone/")

# Формуємо URL сторінки з ноутбуками, використовуючи базовий URL
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/computers/laptops/")

# HTTP-заголовки імітують поведінку реального браузера
HEADERS = {
    # Випадковий User-Agent (Chrome, Firefox, Safari тощо)
    'User-Agent': user_agent.random,
    # Типи контенту, які очікуємо від сервера
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;'
        'q=0.9,image/webp,*/*;q=0.8'
    ),
    # Мова контенту (сервер може повертати різний HTML)
    'Accept-Language': 'en-US,en;q=0.5',
    # З'єднання не закривається одразу, повторне використання TCP-з'єднання
    'Connection': 'keep-alive',
    # Пріоритет HTTPS, якщо доступна версія сторінки
    'Upgrade-Insecure-Requests': '1',
}

def get_home_products() -> list[Product]:
    """
    Завантажує HTML-код головної сторінки магазину
    та повертає список об'єктів Product для подальшої обробки

    Returns:
        list[Product] - список об'єктів Product або None у разі помилки
    """
    try:
        # Виконуємо HTTP GET-запит до головної сторінки
        response = session.get(
            HOME_URL,  # URL сторінки
            headers=HEADERS,  # HTTP-заголовки
            timeout=10,  # Максимальний час очікування відповіді (секунди)
            verify=True  # Перевірка SSL-сертифікату
        )

        # Перевіряємо статус відповіді
        response.raise_for_status()

        # Генеруємо новий User-Agent для наступного запиту
        headers = HEADERS.copy()
        headers["User-Agent"] = user_agent.random

        # Створюємо об'єкт BeautifulSoup для парсингу HTML
        soup = BeautifulSoup(response.content, features="html.parser")

        # Знаходимо всі HTML-блоки товарів
        # ".card-body" - CSS-селектор, який обгортає кожен блок з товаром на сторінці
        products = soup.select(".card-body")

        # Перетворюємо кожен HTML-блок в об'єкт Product
        # - викликаємо parse_single_product
        # - перетворюємо товар в об'єкт Product
        # В результаті отримуємо список готових Python-об'єктів
        return [parse_single_product(product) for product in products]

    # Обробка помилок, пов'язаних з HTTP або мережею
    except requests.exceptions.RequestException as e:
        logging.error(f"Помилка при виконанні запиту до HOME_URL: {e}")
        return []

    except Exception as e:
        logging.warning(f"Неочікувана помилка в get_home_products(): {e}")
        return []

def parse_single_product(product: Tag) -> Product:
    """
    Парсить HTML-блок товару та створює об'єкт Product
    з інформацією про конфігурації та їх ціни
    """
    # Отримуємо ціни конфігурацій за допомогою Selenium
    hdd_prices = parse_hdd_block_prices(product)

    return Product(
        # Назва товару
        # .select_one(".title") - шукає перший елемент з класом "title" всередині блоку товару
        # ["title"] - використовуємо значення HTML-атрибуту title (повна назва)
        title=product.select_one(".title")["title"],

        # Опис товару
        # .text - повертає весь текст всередині HTML-тега
        description=product.select_one(".description").text,

        # Ціна товару
        # .text - отримуємо рядок типу "$123.45"
        # .replace("$", "") - прибираємо символ валюти, щоб залишилися лише цифри
        # float(...) - перетворюємо текст в число з плаваючою крапкою
        price=float(
            product
            .select_one(".price")
            .text
            .replace("$", "")
        ),

        # Рейтинг товару
        # [data-rating] - HTML-атрибут з числовим значенням рейтингу
        # int(...) - перетворюємо текстовий рейтинг в ціле число
        rating=int(
            product
            .select_one("[data-rating]")["data-rating"]
        ),

        # Кількість відгуків
        # .text - рядок типу "12 reviews"
        # .split()[0] - розбиваємо рядок за пробілом та отримуємо перше слово ("12")
        # int(...) - перетворюємо перше слово в число
        num_of_reviews=int(
            product
            .select_one(".review-count")
            .text
            .split()[0]
        ),

        # Додаткова інформація про конфігурації товару
        # Зберігаємо ціни всіх доступних конфігурацій HDD
        additional_info={"hdd_prices": hdd_prices}
    )


def get_laptop_page_products() -> list[Product]:
    """
    Отримує всі товари з усіх сторінок категорії ноутбуків з логуванням.

    Використовує:
    - HTTP-сесію для стабільних запитів
    - Заголовки для імітації браузера
    - Функцію get_single_page_products() для парсингу кожної сторінки
    - Функцію get_num_pages() для визначення загальної кількості сторінок
    - logging для відстеження прогресу та помилок

    Returns:
        list[Product]: Повний список товарів з усіх сторінок
    """
    try:
        # Завантажуємо першу сторінку через HTTP-сесію
        response = session.get(LAPTOP_URL, headers=HEADERS, timeout=10, verify=True)
        response.raise_for_status()

        # Створюємо об'єкт BeautifulSoup для парсингу HTML
        first_page_soup = BeautifulSoup(response.content, features="html.parser")

        # Отримуємо товари з першої сторінки
        all_products = get_single_page_products(first_page_soup)

        # Визначаємо загальну кількість сторінок в категорії
        num_pages = get_num_pages(first_page_soup)
        logging.info(f"Всього знайдено сторінок: {num_pages}")
        logging.info(f"Початок парсингу сторінки 1 з {num_pages}")

        # Обробляємо решту сторінок (починаючи з 2 сторінки)
        for page_num in range(2, num_pages + 1):
            logging.info(f"Початок парсингу сторінки {page_num} з {num_pages}")

            # Завантажуємо наступну сторінку через параметр пагінації
            response = session.get(
                LAPTOP_URL,
                headers=HEADERS,
                params={"page": page_num},  # параметр пагінації
                timeout=10,
                verify=True
            )
            response.raise_for_status()

            # Парсимо наступну сторінку
            next_page_soup = BeautifulSoup(response.content, features="html.parser")
            # Додаємо товари до загального списку all_products
            page_products = get_single_page_products(next_page_soup)
            all_products.extend(page_products)

        logging.info(f"Всього знайдено товарів: {len(all_products)}")
        return all_products

    except requests.exceptions.RequestException as e:
        logging.error(f"Помилка при завантаженні сторінок: {e}")
        return []
    except Exception as e:
        logging.warning(f"Неочікувана помилка: {e}")
        return []


def get_num_pages(page_soup: Tag) -> int:
    """
    Визначає загальну кількість сторінок при пагінації

    Args:
        page_soup: Об'єкт BeautifulSoup з HTML-сторінкою
    Returns:
        int: Кількість сторінок (за замовчуванням 1, якщо пагінація відсутня)
    """

    # Виконуємо пошук контейнера пагінації на сторінці за CSS-класом ".pagination"
    pagination = page_soup.select_one(".pagination")

    # Якщо пагінація не знайдена, повертаємо 1 (одна сторінка)
    if pagination is None:
        return 1

    # Якщо пагінація є:
    # - Беремо всі елементи пагінації (<li>)
    # - Передостанній елемент зазвичай містить номер останньої сторінки (перед кнопкою "Next")
    # - Використання [-2] гарантує, що ми беремо останній номер сторінки, а не кнопку Next.
    # - Конвертуємо текст в ціле число
    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: Tag) -> list[Product]:
    """
    Парсить HTML-сторінку та повертає список товарів.

    Args:
        page_soup: Об'єкт BeautifulSoup з HTML-сторінкою
    Returns:
        list[Product]: Список об'єктів Product з даними про товари
    """

    # Виконуємо пошук всіх контейнерів товарів на сторінці за CSS-класом ".card-body"
    products = page_soup.select(".card-body")

    # Перетворюємо кожен HTML-елемент в об'єкт Product
    return [parse_single_product(product) for product in products]


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    """
    Парсить блок з конфігураціями HDD на сторінці продукту
    та повертає словник {конфігурація: ціна}.

    Функція виконує наступні дії:
    - Переходить на сторінку товару
    - Знаходить блок з кнопками конфігурацій
    - По черзі клікає на кожну активну кнопку
    - Отримує оновлену ціну після кожного кліку
    - Зберігає результат в словник

    Args:
        product_soup: BeautifulSoup об'єкт блоку товару

    Returns:
        dict[str, float]: словник з конфігураціями та їх цінами
                         Порожній словник в разі помилки
    """
    try:
        # Формуємо повну URL-адресу сторінки товару
        # urljoin коректно об'єднує базовий URL з відносним шляхом
        absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])

        # Отримуємо глобальний екземпляр WebDriver
        driver = get_driver()

        # Переходимо на сторінку конкретного товару
        driver.get(absolute_url)

        # Знаходимо блок з кнопками конфігурацій (swatches)
        # .swatches - CSS-клас блоку з варіантами вибору
        swatches = driver.find_element(By.CLASS_NAME, "swatches")

        # Отримуємо всі кнопки конфігурацій з блоку
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        # Словник для зберігання результатів: {конфігурація: ціна}
        prices = {}

        # Перебираємо всі кнопки конфігурацій
        for button in buttons:
            # Перевіряємо, чи кнопка активна (не заблокована)
            if not button.get_property("disabled"):
                # Клікаємо на кнопку для вибору конфігурації
                button.click()

                # Отримуємо оновлену ціну після вибору конфігурації
                price_text = driver.find_element(By.CLASS_NAME, "price").text
                # Прибираємо символ долара та перетворюємо в число
                price_value = float(price_text.replace("$", ""))

                # Отримуємо назву конфігурації з атрибута value кнопки
                config_name = button.get_property("value")

                # Зберігаємо результат у словник
                prices[config_name] = price_value

                # ✅ Логування успішно зчитаної конфігурації та ціни
                logging.info(f"HDD конфігурація '{config_name}' → ${price_value}")

        return prices

    except Exception as e:
        # ⚠️ Логування помилки, якщо не вдалось зчитати блок конфігурацій
        logging.warning(f"Помилка при парсингу HDD блоків: {e}")
        # Повертаємо порожній словник у разі помилки
        return {}

def write_products_to_csv(products: list[Product]) -> None:
    """
    Зберігає список товарів в CSV-файл

    Args:
        products: Список об'єктів Product для збереження
    """
    # Відкриваємо файл для запису
    with open("products.csv", "w", newline='', encoding='utf-8') as f:
        # Створюємо об'єкт writer для запису даних в CSV
        writer = csv.writer(f)

        # Записуємо заголовки стовпців
        writer.writerow(PRODUCT_FIELDS)

        # Записуємо дані кожного товару
        # (astuple перетворює об'єкт Product в кортеж значень)
        writer.writerows([astuple(product) for product in products])


def main():
    """
    Головна функція програми:
    - Ініціалізує WebDriver для динамічного парсингу
    - Отримує список товарів з цінами конфігурацій
    - Зберігає їх у CSV-файл
    - Обробляє помилки та коректно закриває ресурси
    """
    try:
        # Створюємо екземпляр Chrome WebDriver
        # with statement гарантує автоматичне закриття браузера
        with webdriver.Chrome() as driver:
            # Встановлюємо драйвер як глобальний для використання в інших функціях
            set_driver(driver)

            # Отримуємо товари та зберігаємо їх в CSV
            products = get_laptop_page_products()
            write_products_to_csv(products)

            # ✅ Логування успішного завершення парсингу
            logging.info(f"Успішно обработано {len(products)} товарів з конфігураціями")

    # Обробка переривання програми користувачем (Ctrl+C)
    except KeyboardInterrupt:
        logging.warning("Роботу програми перервано користувачем")
    # Обробка будь-яких інших критичних помилок
    except Exception as e:
        logging.critical(f"Критична помилка виконання програми: {e}")
    # Блок finally виконується ЗАВЖДИ, навіть при помилках
    finally:
        # Закриваємо HTTP-сесію для звільнення ресурсів
        session.close()
        logging.info("Ресурси програми успішно звільнено")



if __name__ == "__main__":
    main()
