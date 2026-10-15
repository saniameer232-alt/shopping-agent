from . import llm
from .understand import understand
from .retrieve import load_catalog, retrieve
from .rank import rank
from .respond import build_reply, clarifying_question, polish


class ShoppingAgent:
    def __init__(self, catalog_path: str = "data/catalog.json", use_llm: bool = True):
        self.catalog = load_catalog(catalog_path)
        self.use_llm = use_llm and llm.available()
        self.pending = None

    def chat(self, message: str) -> str:
        text = f"{self.pending}. {message}" if self.pending else message
        q = understand(text)

        if q.vague:
            self.pending = text
            return clarifying_question(text)

        self.pending = None
        results = rank(retrieve(self.catalog, q), q)
        reply = build_reply(results, q)

        if self.use_llm:
            try:
                reply = polish(reply)
            except Exception as e:
                print("LLM polish failed:", e)   # fallback: template wala jawab
        return reply