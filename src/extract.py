import re
from . import llm
from .schema import Product, ProductAttributes

# ---------- Keyword tables: "naam": "pattern" ----------
MATERIALS = {
    "mesh": r"\bmesh", "knit": r"\bknit", "canvas": r"canvas",
    "synthetic leather": r"synthetic leather", "leather": r"(?<!synthetic )leather",
    "rubber": r"rubber", "nylon": r"nylon", "polyester": r"polyester",
    "cotton": r"cotton", "stainless steel": r"stainless steel",
    "aluminum": r"aluminum", "TPU": r"\btpu\b", "foam": r"\bfoam", "fleece": r"fleece",
}

USES = {
    "road running": r"road", "trail": r"trail", "racing": r"racing",
    "casual": r"casual|everyday", "commuting": r"commut", "hiking": r"hik|trek",
    "fitness": r"fitness|\bgps\b", "wet weather": r"wet weather|rain",
    "travel": r"travel", "swimming": r"swim",
}

FEATURES = {
    "wireless": r"wireless|bluetooth", "anc": r"noise cancel",
    "charging_case": r"charging case|case battery", "sweat_resistant": r"ipx\d|sweat",
    "spatial_audio": r"spatial audio", "wireless_charging": r"wireless charging",
    "gps": r"\bgps\b", "heart_rate": r"heart rate", "laptop_sleeve": r"laptop sleeve",
    "packable": r"packable", "warm": r"warm|fleece", "breathable": r"breathable",
}

# category ke hisaab se "lightweight" ki hadd (ounces mein)
LIGHT_OZ = {"running shoes": 9.5, "sneakers": 9.0, "backpacks": 20, "jackets": 12}

# ---------- Review patterns ----------
# pani andar aane ke alfaaz
CONTRA = re.compile(
    r"soak|leak|(get|gets|got) wet|water (gets|got|came|comes) in|lets? water|wets? through",
    re.I,
)
# "didn't leak", "not soaked" jaise positive jumle ignore karne ke liye
NEG_GUARD = re.compile(r"(no|never|didn'?t|did not|doesn'?t|not) (\w+ )?(leak|soak)", re.I)
# durability ke masle
DURA = re.compile(r"fall(s|ing)? apart|fell apart|came apart|peel|broke|loosen|tore|ripped", re.I)


def extract_heuristic(row: dict) -> ProductAttributes:
    desc = row["description"].lower()
    reviews = [r.strip() for r in row["reviews"].split("||") if r.strip()]

    # 1) Description kya claim karti hai?
    if re.search(r"(?<!not )waterproof", desc):
        water = "waterproof"
    elif re.search(r"water[- ]resistant|weatherproof|ipx|\d\s?atm", desc):
        water = "water_resistant"
    else:
        water = "none"

    # 2) Weight nikalo aur lightweight tay karo
    m = re.search(r"(\d+(?:\.\d+)?)\s*(oz|lbs?)\b", desc)
    oz = None
    if m:
        oz = float(m.group(1)) * (16 if m.group(2).startswith("lb") else 1)
    limit = LIGHT_OZ.get(row["category"])
    lightweight = bool(re.search(r"lightweight|ultralight|ultra-light|packable", desc)) \
        or bool(oz and limit and oz <= limit)

    # 3) Features
    features = [name for name, pat in FEATURES.items() if re.search(pat, desc)]
    hours = re.search(r"(\d+)[- ]hour", desc)
    if hours and int(hours.group(1)) >= 8:
        features.append("long_battery")

    # 4) Description vs reviews ka tazad
    contradiction = water != "none" and any(
        CONTRA.search(r) and not NEG_GUARD.search(r) for r in reviews
    )

    return ProductAttributes(
        water=water,
        lightweight=lightweight,
        weight_oz=oz,
        materials=[n for n, p in MATERIALS.items() if re.search(p, desc)],
        intended_use=[n for n, p in USES.items() if re.search(p, desc)],
        features=features,
        review_waterproof_contradiction=contradiction,
        review_durability_issue=any(DURA.search(r) for r in reviews),
        review_summary=" / ".join(reviews[:2]),
    )


SYSTEM = """You extract product attributes. Return ONLY JSON with these keys:
water: "waterproof" | "water_resistant" | "none"  (what the DESCRIPTION claims),
lightweight: true ONLY if the description says lightweight/ultralight or states a weight that is
  clearly light for its category. If no weight or claim is stated, use false. Never guess.
weight_oz: number or null,
materials: list of strings, intended_use: list of strings,
features: list chosen from [wireless, anc, charging_case, long_battery, sweat_resistant,
  spatial_audio, wireless_charging, gps, heart_rate, laptop_sleeve, packable, warm, breathable],
review_waterproof_contradiction: true ONLY if the description claims waterproof/water-resistant
  but reviews say water gets in, it leaks or soaks,
review_durability_issue: true ONLY if a review explicitly says it fell apart, broke, peeled,
  tore or loosened. Complaints like "feels cheap" or "tangles" do NOT count.
review_summary: max 25 words."""


def extract_product(row: dict, use_llm: bool = True) -> Product:
    attrs = None
    if use_llm and llm.available():
        try:
            data = llm.chat_json(
                SYSTEM,
                f"Category: {row['category']}\nDescription: {row['description']}\nReviews: {row['reviews']}")
            attrs = ProductAttributes(**data)     # schema validation
        except Exception as e:
            print(f"  LLM failed for {row['title']} ({e}); using rules")
    attrs = attrs or extract_heuristic(row)       # fallback
    return Product(
        id=int(row["id"]), title=row["title"], category=row["category"],
        price=float(row["price"]), rating=float(row["rating"]),
        **attrs.model_dump(),
    )