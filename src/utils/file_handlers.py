import csv
from dataclasses import astuple
from pathlib import Path

from src.models import PRODUCT_FIELDS, Product

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
CSV_PATH = DATA_DIR / "products.csv"


def write_products_to_csv(products: list[Product]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])

