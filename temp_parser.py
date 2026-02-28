# Бібліотека для виконання HTTP-запитів (GET, POST тощо)
# Використовується для завантаження HTML-сторінок
import requests

# BeautifulSoup - бібліотека для парсингу HTML та XML
# Дозволяє зручно працювати з тегами, класами, атрибутами
from bs4 import BeautifulSoup

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

def get_home_products():
    """
    Завантажує HTML-код головної сторінки магазину
    та повертає об'єкт BeautifulSoup для подальшого парсингу

    Returns:
        BeautifulSoup | None
    """
    try:
        # Виконуємо HTTP GET-запит до головної сторінки
        response = session.get(
            HOME_URL,  # URL сторінки
            headers=HEADERS,  # HTTP-заголовки
            timeout=10,  # Максимальний час очікування відповіді (секунди)
            verify=True  # Перевіряти SSL-сертифікат
        )

        # Перевіряємо статус відповіді
        # Якщо код 4xx або 5xx - буде згенеровано виняток
        response.raise_for_status()

        # Оновлюємо User-Agent для наступного запиту,
        # щоб кожен запит виглядав як новий користувач
        headers = HEADERS.copy()
        headers["User-Agent"] = user_agent.random

        # Створимо об'єкт BeautifulSoup
        # response.content - байти HTML, не залежить від кодування
        # (більш надійно, ніж response.text, який декодує в str)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Виводимо HTML-код з відступами
        # ⚠️ Для великих сторінок краще закоментувати
        print(soup.prettify())

        # Повертаємо об'єкт BeautifulSoup
        return soup

    # Обробка помилок, пов'язаних з HTTP або мережею
    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка при виконанні запиту: {e}")
        return None
    # Обробка будь-яких інших неочікуваних помилок
    except Exception as e:
        print(f"⚠️ Неочікувана помилка: {e}")
        return None

def main():
    """
    Головна функція програми
    Викликає основну логіку та закриває ресурси
    """
    try:
        # Отримуємо HTML-дані головної сторінки
        soup = get_home_products()
        return soup

    # Якщо користувач натиснув Ctrl + C
    except KeyboardInterrupt:
        print("\n🛑 Роботу програми перервано користувачем")
    # Ловимо будь-яку критичну помилку
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
    # Блок finally виконується ЗАВЖДИ
    finally:
        # Закриваємо HTTP-сесію
        session.close()

if __name__ == "__main__":
    main()
