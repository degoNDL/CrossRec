"""Cache simples em disco para respostas do LLM, chaveado por hash do
prompt. Chamadas de LLM custam dinheiro e tempo — sem isso, repetir a
mesma pergunta (comum em testes manuais e em uso real, ex: o mesmo pedido
de dois turistas parecidos) bateria a API toda vez à toa.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache" / "ai"


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def get_cached(key: str) -> Any | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def set_cached(key: str, value: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
