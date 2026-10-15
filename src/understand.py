import re
from .schema import Query

# (category ka naam, usay pakadne wala pattern)
CATEGORY_PATTERNS = [
    ("sneakers", r"sneaker|trainer"),
    ("running shoes", r"running shoe|runner|jogging|\bshoes?\b"),
    ("earbuds", r"earbud|earphone|airpod|headphone"),
    ("backpacks", r"backpack|rucksack|\bbag\b"),
    ("watches", r"watch|smartwatch|fitness band|tracker"),
    ("jackets", r"jacket|raincoat|parka|coat"),
]

# need ka naam -> pattern
NEED_PATTERNS = {
    "waterproof": r"water[- ]?proof",
    "water_resistant": r"water[- ]resistant|\brain\b|drizzle|wet weather|splash",
    "lightweight": r"lightweight|ultralight|\blight\b(?! rain)",
    "durable": r"durab|fall(ing)? apart|last long|holds? up|sturdy|won'?t break",
    "anc": r"noise[- ]cancel|\banc\b",
    "wireless": r"wireless|bluetooth",
}

BASIC_PATTERN = r"cheap|basic|budget|simple|inexpensive|no[- ]frills"
PRICE_PATTERNS = [
    r"(?:under|below|less than|up to|max(?:imum)?|within|<)\s*\$?\s*(\d+(?:\.\d+)?)",
    r"\$\s*(\d+(?:\.\d+)?)",
]


def understand(text: str) -> Query:
    t = text.lower()

    # 1) category
    category = None
    for name, pattern in CATEGORY_PATTERNS:
        if re.search(pattern, t):
            category = name
            break

    # 2) budget
    max_price = None
    for pattern in PRICE_PATTERNS:
        m = re.search(pattern, t)
        if m:
            max_price = float(m.group(1))
            break

    # 3) needs
    needs = [n for n, p in NEED_PATTERNS.items() if re.search(p, t)]
    if "waterproof" in needs and "water_resistant" in needs:
        needs.remove("water_resistant")   # waterproof zyada strong hai

    # 4) basic / cheap?
    wants_basic = bool(re.search(BASIC_PATTERN, t))

    # 5) vague: category hi nahi pata to hum guess nahi karenge
    vague = category is None

    return Query(category=category, max_price=max_price, needs=needs,
                 wants_basic=wants_basic, vague=vague, raw=text)