import re
from . import llm

FEATURE_LABEL = {
    "anc": "active noise cancellation", "charging_case": "a charging case",
    "sweat_resistant": "sweat resistance", "long_battery": "long battery life",
    "spatial_audio": "spatial audio", "wireless_charging": "wireless charging",
    "gps": "built-in GPS", "heart_rate": "heart-rate tracking",
    "laptop_sleeve": "a laptop sleeve", "packable": "a packable design",
    "warm": "extra warmth", "breathable": "breathable fabric",
    "wireless": "wireless connectivity",
}
NEED_LABEL = {
    "waterproof": "waterproof", "water_resistant": "water-resistant",
    "lightweight": "lightweight", "durable": "durable",
    "anc": "noise-cancelling", "wireless": "wireless",
}


def money(x: float) -> str:
    return f"${x:,.0f}" if float(x).is_integer() else f"${x:,.2f}"


def join(items: list) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def clarifying_question(text: str) -> str:
    t = text.lower()
    cats = "running shoes, sneakers, earbuds, backpacks, watches or jackets"
    if re.search(r"\bmom\b|mother|\bdad\b|father|gift|wife|husband|friend|sister|brother", t):
        return ("Happy to help you find something! To pick well, could you tell me "
                "what kind of thing they would enjoy and your rough budget? "
                f"I can help with {cats}.")
    return ("I'd love to help. What kind of product are you looking for, "
            f"and do you have a budget in mind? I can help with {cats}.")


def build_reply(res, q) -> str:
    if res.top is None:
        return "Sorry, I couldn't find a matching product. Could you rephrase or relax a requirement?"

    t = res.top
    p = t.product
    lines = []

    # 1) top pick
    if t.matches:
        labels = [NEED_LABEL.get(n, n) for n in t.matches]
        lines.append(f"My top pick is the **{p.title}** ({money(p.price)}). "
                     f"It's {join(labels)} and rated {p.rating}/5 by reviewers.")
    else:
        lines.append(f"The closest match I found is the **{p.title}** ({money(p.price)}), "
                     f"rated {p.rating}/5.")

    # 2) trade-offs
    if t.misses:
        lines.append("Heads up: it isn't " + join([NEED_LABEL.get(n, n) for n in t.misses]) + ".")
    if t.over_budget > 0:
        lines.append(f"It's {money(t.over_budget)} over your {money(q.max_price)} budget, "
                     "but it's the best fit for your other requirements.")
    for w in t.warnings:
        lines.append(f"⚠️ Reviewers' warning: {w}.")

    # 3) backups
    if res.alternatives:
        lines.append("\nOther options:")
        for a in res.alternatives:
            note = ""
            if a.misses:
                note = " (but it isn't " + join([NEED_LABEL.get(n, n) for n in a.misses]) + ")"
            lines.append(f"- **{a.product.title}** ({money(a.product.price)}){note}")

    # 4) upsell
    if res.upsell:
        diff = res.upsell.price - p.price
        gains = [FEATURE_LABEL.get(g, g) for g in res.upsell_gains[:3]]
        lines.append(f"\n💡 Worth stretching? For {money(diff)} more, the **{res.upsell.title}** "
                     f"({money(res.upsell.price)}) adds {join(gains)}.")

    # 5) jo products claim karte hain lekin reviews jhutlate hain
    for b in res.avoid:
        lines.append(f"\n🚫 I'd skip the **{b.product.title}**: {b.warnings[0]}.")

    return "\n".join(lines)


def polish(draft: str) -> str:
    system = (
        "You are a friendly sales associate. Rewrite the draft reply so it sounds natural "
        "and conversational. Keep EVERY product name, price, number and warning exactly "
        "as in the draft. Do NOT add any product, price or claim that is not in the draft. "
        "Keep product names in **bold**. Keep it concise."
    )
    return llm.chat(system, draft, temperature=0.4)