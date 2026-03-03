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
from dataclasses import dataclass

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
        print(f"❌ Помилка при виконанні запиту: {e}")
        return None
    # Обробка будь-яких інших неочікуваних помилок
    except Exception as e:
        print(f"⚠️ Неочікувана помилка: {e}")
        return None

    # Обробка помилок, пов'язаних з HTTP або мережею
    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка при виконанні запиту: {e}")
        return None
    # Обробка будь-яких інших неочікуваних помилок
    except Exception as e:
        print(f"⚠️ Неочікувана помилка: {e}")
        return None

def parse_single_product(product: Tag) -> Product:
    return Product(
        # Назва товару
        # .select_one(".title") - шукає перший елемент з класом "title" всередині блоку товару
        # ["title"] - використовуємо значення HTML-атрибуту 'title'
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
        )
    )



def main():
    """
    Головна функція, яка керує логікою роботи парсера
    Виконує отримання даних, обробку помилок та закриття ресурсів.
    """
    try:
        # Отримуємо список товарів
        products = get_home_products()

        if products:
            print("✅ Дані успішно отримано та оброблено!\n")

            # Виводимо інформацію про перші 3 товари для перевірки
            for index, product in enumerate(products, 1):
                print(f"{index}. {product}")
        else:
            print("❌ Не вдалося отримати дані. Перевірте підключення або спробуйте пізніше.")

    except KeyboardInterrupt:
        print("\n🛑 Роботу програми перервано користувачем.")
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
    finally:
        # Обов'язково закриваємо сесію
        session.close()

if __name__ == "__main__":
    main()
