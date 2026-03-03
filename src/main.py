from __future__ import annotations

import sys
from pathlib import Path
import logging

from selenium import webdriver

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.scraper import close_session, get_laptop_page_products
from src.utils.file_handlers import write_products_to_csv
from src.utils.logger import configure_logging
from src.utils.selenium_utils import set_driver


def main() -> None:
    try:
        with webdriver.Chrome() as driver:
            set_driver(driver)
            products = get_laptop_page_products()
            write_products_to_csv(products)
            logging.info(f"Успішно оброблено {len(products)} товарів з конфігураціями")
    except KeyboardInterrupt:
        logging.warning("Роботу програми перервано користувачем")
    except Exception as error:
        logging.critical(f"Критична помилка виконання програми: {error}")
    finally:
        close_session()
        logging.info("Ресурси програми успішно звільнено")


def run() -> None:
    configure_logging()
    main()


if __name__ == "__main__":
    run()
