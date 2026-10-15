import json
from .schema import Product, Query


def load_catalog(path: str = "data/catalog.json") -> list[Product]:
    with open(path, encoding="utf-8") as f:
        return [Product(**p) for p in json.load(f)]


def retrieve(catalog: list[Product], q: Query) -> list[Product]:
    """Candidates chunna: agar category pata hai to sirf usi category ke products."""
    if q.category:
        return [p for p in catalog if p.category == q.category]
    return list(catalog)