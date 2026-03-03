from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    if _driver is None:
        raise RuntimeError("WebDriver не ініціалізований.")
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver
