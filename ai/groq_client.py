"""Cliente Groq compartilhado. Lê a chave de `.env` (nunca commitado — ver
`.env.example`) via `python-dotenv`, e cria o client uma única vez.
"""

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY não configurada. Copie .env.example para .env e "
                "preencha com sua chave (console.groq.com)."
            )
        _client = Groq(api_key=api_key)
    return _client
