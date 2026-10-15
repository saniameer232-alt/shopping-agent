from dataclasses import dataclass, field
from typing import Optional
from .schema import Product, Query

# upsell mein kaun si feature zyada qeemti hai
FEATURE_WEIGHT = {"anc": 3, "gps": 2, "heart_rate": 2, "spatial_audio": 2, "wireless_charging": 1.5}


@dataclass
class Ranked:
    product: Product
    score: float
    matches: list = field(default_factory=list)    # jo needs poori hui
    misses: list = field(default_factory=list)     # jo needs poori nahi hui
    warnings: list = field(default_factory=list)   # reviews ki warning
    contradiction: bool = False                    # description vs reviews ka tazad
    over_budget: float = 0.0                       # budget se kitna zyada


@dataclass
class RankResult:
    top: Optional[Ranked]
    alternatives: list
    upsell: Optional[Product]
    upsell_gains: list
    avoid: list


def check_need(p: Product, need: str) -> str:
    """Return 'yes', 'partial' ya 'no'."""
    if need == "waterproof":
        if p.water == "waterproof":
            return "yes"
        return "partial" if p.water == "water_resistant" else "no"
    if need == "water_resistant":
        return "yes" if p.water != "none" else "no"
    if need == "lightweight":
        return "yes" if p.lightweight else "no"
    if need == "durable":
        return "no" if p.review_durability_issue else "yes"
    return "yes" if need in p.features else "no"      # anc, wireless


def score_product(p: Product, q: Query) -> Ranked:
    score = p.rating                      # base: rating (0-5)
    r = Ranked(product=p, score=0)

    # 1) har need ke liye points
    for need in q.needs:
        res = check_need(p, need)
        if res == "yes":
            score += 1 if need == "durable" else 3
            r.matches.append(need)
        elif res == "partial":
            score -= 2
            r.misses.append(need)
        else:
            score -= 4
            r.misses.append(need)

    # 2) review contradiction: description kuch aur, reviews kuch aur
    wants_water = "waterproof" in q.needs or "water_resistant" in q.needs
    if wants_water and p.review_waterproof_contradiction:
        score -= 8
        r.contradiction = True
        r.warnings.append("claims water protection, but reviewers say water gets in")
    if "durable" in q.needs and p.review_durability_issue:
        r.warnings.append("reviewers report it falling apart")

    # 3) budget
    if q.max_price:
        if p.price <= q.max_price:
            score += 2
        elif p.price <= q.max_price * 1.25:      # thora sa upar: allowed lekin flag
            score -= 1
            r.over_budget = p.price - q.max_price
        else:
            score -= 6
            r.over_budget = p.price - q.max_price

    # 4) "cheap/basic" maange to sasta behtar
    if q.wants_basic:
        score -= p.price / 20

    r.score = score
    return r


def find_upsell(top: Ranked, ranked: list, q: Query):
    """Thora mehnga product jo sach mein zyada benefit de."""
    if top.contradiction:
        return None, []
    tp = top.product
    best = None
    for r in ranked:
        p = r.product
        if p.id == tp.id or p.price <= tp.price or r.contradiction or p.rating < tp.rating:
            continue
        if p.price > min(tp.price * 2.5, tp.price + 40):      # "slightly" mehnga
            continue
        if q.max_price and p.price > q.max_price * 1.25:
            continue
        if r.misses:                                          # user ki needs poori karta ho
            continue
        gains = [f for f in p.features if f not in tp.features]
        if not gains:
            continue
        key = (sum(FEATURE_WEIGHT.get(f, 1) for f in gains), -p.price)
        if best is None or key > best[0]:
            best = (key, p, gains)
    if not best:
        return None, []
    gains = sorted(best[2], key=lambda f: -FEATURE_WEIGHT.get(f, 1))
    return best[1], gains


def rank(candidates: list, q: Query) -> RankResult:
    ranked = sorted((score_product(p, q) for p in candidates),
                    key=lambda r: r.score, reverse=True)
    if not ranked:
        return RankResult(None, [], None, [], [])
    top = ranked[0]
    upsell, gains = find_upsell(top, ranked, q)
    alternatives = [r for r in ranked[1:]
                    if not r.contradiction and r.score > 0
                    and not (upsell and r.product.id == upsell.id)
                    and (not q.wants_basic or r.product.price <= top.product.price * 2.5)][:2]
    avoid = [r for r in ranked[1:] if r.contradiction]
    return RankResult(top, alternatives, upsell, gains, avoid)