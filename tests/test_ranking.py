from src.understand import understand
from src.retrieve import load_catalog, retrieve
from src.rank import rank
from src.agent import ShoppingAgent

catalog = load_catalog()


def run(text):
    q = understand(text)
    return q, rank(retrieve(catalog, q), q)


def test_a_specific_match():
    q, res = run("I need a lightweight waterproof running shoe, ideally under $80.")
    assert res.top.product.title == "AquaShield Trail"
    assert res.top.over_budget == 9
    assert any(a.product.title == "StrideLite Run 2" for a in res.alternatives)
    assert any(b.product.title == "LeakGuard Runner" for b in res.avoid)


def test_b_ambiguity_asks_question():
    q = understand("Something nice for my mom.")
    assert q.vague
    reply = ShoppingAgent(use_llm=False).chat("Something nice for my mom.")
    assert "?" in reply and "**" not in reply      # sawal poochha, product nahi dikhaya


def test_b_followup_gives_recommendation():
    agent = ShoppingAgent(use_llm=False)
    agent.chat("Something nice for my mom.")
    reply = agent.chat("earbuds under $50")
    assert "**" in reply                           # ab product recommend hua


def test_c_review_contradiction():
    q, res = run("Casual sneaker that won't fall apart in light rain.")
    assert res.top.product.title == "TrailCasual Weather"
    assert any(b.product.title == "CityStep Water-Resistant" for b in res.avoid)


def test_d_upsell():
    q, res = run("Cheap wireless earbuds, just need something basic.")
    assert res.top.product.title == "BudBasic Wireless"
    assert res.upsell.title == "QuietPods ANC"
    assert "anc" in res.upsell_gains