"""Traduz o desejo do turista em linguagem natural ("quero ver o centro
histórico e terminar numa praia") para uma lista concreta de ids do
catálogo curado — a ponte entre o pedido livre e o otimizador, que só
entende ids.
"""

import json
import re

from ai.cache import get_cached, set_cached
from ai.groq_client import MODEL, get_client

SYSTEM_PROMPT = """Você traduz o desejo de um turista em Recife para uma lista de ids \
de um catálogo fixo de pontos turísticos.

Responda SOMENTE com um objeto JSON no formato exato:
{"pontos_ids": ["id-do-ponto-1", "id-do-ponto-2"]}

Regras:
- Use APENAS ids que aparecem no catálogo fornecido, exatamente como escritos.
- Escolha os pontos que melhor combinam com o pedido do turista, mesmo que ele \
não cite nomes exatos (ex: "centro histórico" deve puxar pontos de categoria \
histórico/cultural/religioso do centro).
- Se nada do catálogo combinar bem com o pedido, devolva {"pontos_ids": []}.
- Não invente ids que não estão no catálogo. Não escreva nada fora do JSON."""

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def _resumo_catalogo(catalogo: list[dict]) -> str:
    return "\n".join(f"- {p['id']}: {p['nome']} ({p['categoria']})" for p in catalogo)


def _extrair_json(texto: str) -> dict:
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK_RE.search(texto)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Resposta do LLM não é um JSON válido: {texto!r}")


def traduzir_desejo(texto_usuario: str, catalogo: list[dict]) -> list[str]:
    """Retorna os ids do catálogo que melhor atendem ao pedido em texto
    livre. Ids que o LLM eventualmente inventar são descartados — a lista
    devolvida é sempre um subconjunto válido do catálogo."""

    texto_normalizado = texto_usuario.strip().lower()
    cache_key = f"nl_to_points:{MODEL}:{texto_normalizado}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached["pontos_ids"]

    prompt_usuario = (
        f"Catálogo de pontos disponíveis:\n{_resumo_catalogo(catalogo)}\n\n"
        f'O que o turista quer: "{texto_usuario}"'
    )

    resposta = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_usuario},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    conteudo = resposta.choices[0].message.content
    dados = _extrair_json(conteudo)
    ids_sugeridos = dados.get("pontos_ids", [])

    ids_validos = {p["id"] for p in catalogo}
    ids_filtrados = [pid for pid in ids_sugeridos if pid in ids_validos]

    set_cached(cache_key, {"pontos_ids": ids_filtrados})
    return ids_filtrados
