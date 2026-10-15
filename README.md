# Conversational Product Search & Recommendation Agent

A chat agent that sits between a shopper and a product catalog. Instead of simple keyword
search, it understands messy natural-language requests, extracts structured attributes from
product descriptions and reviews, and returns a ranked, conversational recommendation.

Ranking is rule-based (fast, predictable, unit-tested). An LLM (Groq) is used only for
attribute extraction and for making replies sound natural. If the LLM is unavailable, the
agent falls back to rules and keeps working.

## Features

- **Attribute extraction**: turns descriptions and reviews into structured JSON (water
  resistance, weight, materials, intended use, features).
- **Query understanding**: pulls category, budget and needs (waterproof, lightweight, ...) from free text.
- **Retrieval and ranking**: scores products against the shopper's needs and budget.
- **Review contradiction handling**: down-ranks products whose reviews contradict their description.
- **Ambiguity handling**: detects vague queries and asks a clarifying question instead of guessing.
- **Upselling**: suggests a slightly pricier product with a clear, benefit-driven reason.
- **Chat UI**: Streamlit web app plus a terminal chat.

## Project structure

```
shopagent/
├── app.py                  # Streamlit chat UI
├── chat_cli.py             # Terminal chat
├── build_catalog.py        # products.csv -> data/catalog.json
├── compare_catalogs.py     # Compare rules vs LLM extraction
├── requirements.txt
├── .env.example            # Template for the API key file
├── data/
│   ├── products.csv        # Raw catalog (25 products)
│   └── catalog.json        # Structured catalog (generated)
├── src/
│   ├── schema.py           # Data models (pydantic)
│   ├── llm.py              # Groq client (OpenAI-compatible API)
│   ├── extract.py          # Description + reviews -> attributes (LLM, rules fallback)
│   ├── understand.py       # Query -> category, budget, needs, vagueness
│   ├── retrieve.py         # Candidate search
│   ├── rank.py             # Scoring, contradiction penalty, upsell
│   ├── respond.py          # Reply generation (+ optional LLM polish)
│   └── agent.py            # Orchestrates the whole pipeline
└── tests/
    └── test_ranking.py     # Tests for the four core scenarios
```

## Approach

The agent is a pipeline of small modules, each with one job:

```
User message
    -> understand.py   (category, budget, needs; vague? -> ask a question)
    -> retrieve.py     (candidate products from data/catalog.json)
    -> rank.py         (score, penalize contradictions, pick upsell)
    -> respond.py      (draft reply; LLM rewrites wording only)
    -> Reply
```

1. **Extraction (offline).** `build_catalog.py` passes every product's description and
   reviews through `extract.py`, validates the result with a pydantic schema and saves it to
   `data/catalog.json`. Doing this offline keeps chat-time answers fast, cheap and repeatable.
2. **Query understanding.** `understand.py` turns a message into category, budget, needs, a
   "wants basic/cheap" flag and a vagueness flag.
3. **Retrieval and ranking.** `retrieve.py` selects candidates by category. `rank.py` scores
   each one, penalizes contradictions and picks an upsell.
4. **Response.** `respond.py` builds the reply from the ranked result and an LLM can reword
   it. `agent.py` ties everything together and remembers the previous message after a
   clarifying question.

The key design decision is a **hybrid**: ranking is deterministic code so it can be tested,
while the LLM never decides which product wins. It is told not to add products, prices or
claims that are not in the draft.

## Setup

1. Create and activate a virtual environment:

```
   python -m venv venv
   venv\Scripts\activate          # Windows
   # source venv/bin/activate     # macOS / Linux
```

2. Install dependencies:

```
   pip install -r requirements.txt
```

3. Create a `.env` file in the project root (copy `.env.example`) and add your Groq API key:

```
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=openai/gpt-oss-20b
```

   The key is optional: without it the agent runs in rules-only mode. Model availability
   changes over time. To see which models your key can use, call Groq's
   `/openai/v1/models` endpoint and set `GROQ_MODEL` accordingly.

## Usage

```
python build_catalog.py            # build the structured catalog (LLM, rules as fallback)
python build_catalog.py --rules    # rules only, no API calls
python -m streamlit run app.py     # chat UI in the browser
python chat_cli.py                 # chat in the terminal
python -m pytest tests -v          # run the tests
```

> On Windows, prefer `python -m streamlit` and `python -m pytest` over calling `streamlit` /
> `pytest` directly. This avoids broken launchers if the virtual environment was created in
> a differently named folder.

## How each scenario is handled

**A. Specific match**: "I need a lightweight waterproof running shoe, ideally under $80."
`understand.py` extracts category = running shoes, max price = 80, needs = waterproof +
lightweight. In `rank.py`, meeting a need adds points, missing one subtracts points, and a
product up to 25% over budget is allowed but flagged. The agent recommends the $89
waterproof shoe, says it is $9 over budget, and offers a $64 backup while stating that the
backup is not waterproof.

**B. Ambiguity**: "Something nice for my mom."
No category is found, so the query is marked vague. `agent.py` stops before retrieval and
`respond.py` asks a clarifying question. The question is stored as pending, so the next
message ("earbuds under $50") is combined with the first one.

**C. Review contradiction**: "Casual sneaker that won't fall apart in light rain."
During extraction, a product that claims water resistance but whose reviews mention water
getting in gets `review_waterproof_contradiction = true`. In `rank.py` this costs a heavy
penalty (-8), so the product sinks and the reply warns the shopper to skip it. Reviews that
report a product falling apart are flagged separately as a durability issue.

**D. Intelligent upsell**: "Cheap wireless earbuds, just need something basic."
The cheapest good match is shown first. `find_upsell` in `rank.py` looks for a product that
is only slightly more expensive (at most 2.5x or +$40), has no contradiction, meets all the
shopper's needs and adds at least one new feature. Features have weights, so active noise
cancellation counts for more than a charging case. The reply states the price difference
and the concrete benefit.

## Rules vs LLM extraction

I built two extractors: regex rules (`extract_heuristic`) and an LLM (Groq) with schema
validation, falling back to the rules if a call fails or returns invalid JSON. Comparing
both on the 25 products with `compare_catalogs.py`:

- They agreed on every water-related field, including all review contradictions.
- They disagreed on 4 attributes. In three of them the LLM guessed something the text did
  not say (calling basic earbuds "lightweight" with no weight stated, treating "cable
  tangles" and "zippers feel cheap" as durability failures). One case (a 14 oz fleece jacket
  counted as lightweight) is debatable, because my weight threshold is itself hand-picked.
- I tightened the extraction prompt to say "never guess" and to count only explicit failures
  (fell apart, broke, peeled) as durability problems.
  <!-- TODO: re-run `python compare_catalogs.py` and write the new number of differences here, then delete this comment -->

Lesson: the LLM handles unusual wording better, but needs strict instructions and
validation, because it tends to fill gaps with plausible guesses.

## Tradeoffs and limitations

- **Hand-tuned weights**: the scoring values (+3, -4, -8, the 25% budget margin, the upsell
  limits) were chosen by hand and checked against the four scenarios, not learned from data.
- **Small dataset**: 25 products and 6 categories; the ranking has not been tested at scale.
- **Rule-based understanding**: `understand.py` uses keyword patterns, so unusual phrasing
  ("bone dry", "drenched") can be missed.
- **Contradiction detection**: it relies on keywords in reviews ("leaks", "soaked"), so a
  paraphrased complaint could slip through.
- **LLM variability**: reworded replies can differ between runs, so tests run with the LLM
  disabled. Model availability also changes over time: the first model I tried
  (`llama-3.3-70b-versatile`) was not available on my account, so I listed the available
  models through Groq's API and switched to `openai/gpt-oss-20b`.
- **Fallbacks**: if extraction or rewording fails, the agent uses the rule-based path, so it
  keeps working without an API key.

## What I would do next

- Use embeddings for semantic retrieval instead of category filtering.
- Add an LLM-based query-understanding step with the same validation and fallback.
- Calibrate the scoring weights from real shopper feedback.
- Expand the catalog and add more categories.
- Support multi-turn refinement ("something cheaper", "in black").

## Testing

`tests/test_ranking.py` has 5 tests that check the four scenarios programmatically
(specific match, ambiguity, the follow-up after a clarifying question, review contradiction,
upsell). They run with the LLM disabled so results are deterministic:

```
python -m pytest tests -v
```

## Security

Never commit your `.env` file or share your API key. `.env` and `venv/` should be listed in
`.gitignore`.