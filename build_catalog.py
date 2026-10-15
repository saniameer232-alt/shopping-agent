import csv
import json
import sys
from src.extract import extract_product

use_llm = "--rules" not in sys.argv

with open("data/products.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

catalog = []
for r in rows:
    print("extracting", r["title"])
    catalog.append(extract_product(r, use_llm).model_dump())

with open("data/catalog.json", "w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2)

print(f"Saved {len(catalog)} products -> data/catalog.json")