from dataclasses import dataclass, fields


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict[str, dict[str, float]]


PRODUCT_FIELDS = [field.name for field in fields(Product)]

