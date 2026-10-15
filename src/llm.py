import os
import json
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def available() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def _client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("GROQ_API_KEY"),
                  base_url="https://api.groq.com/openai/v1")


def chat(system: str, user: str, temperature: float = 0.3) -> str:
    r = _client().chat.completions.create(
        model=MODEL, temperature=temperature,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return r.choices[0].message.content.strip()


def chat_json(system: str, user: str) -> dict:
    r = _client().chat.completions.create(
        model=MODEL, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return json.loads(r.choices[0].message.content)