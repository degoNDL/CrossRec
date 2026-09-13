"""Narra o roteiro já otimizado em texto corrido e acolhedor — a ordem e os
horários vêm prontos e corretos do otimizador (Fase 3); o LLM só veste isso
com uma dica por parada e uma sugestão de almoço. O LLM não decide nada
sobre a rota em si, só narra o que já foi calculado.
"""

import hashlib

from ai.cache import get_cached, set_cached
from ai.groq_client import MODEL, get_client

SYSTEM_PROMPT = """Você é um guia local acolhedor do Recife, Brasil. Você recebe um \
roteiro de um dia já calculado (ordem das paradas, horários e modo de transporte) e \
escreve um texto corrido em português do Brasil contando o dia do turista.

Regras:
- NÃO mude a ordem, os horários ou o modo de transporte — eles já foram calculados \
e são fixos. Sua única tarefa é narrar.
- Para cada parada, escreva 1-2 frases com uma dica prática ou curiosidade real e \
plausível sobre o lugar.
- Sugira um TIPO de comida ou prato típico pernambucano para o almoço (ex: "um \
restaurante de comida nordestina", "uma tapiocaria"), encaixado no horário que \
fizer sentido dentro do itinerário (normalmente entre 11h30 e 14h). NÃO invente \
o NOME de um restaurante específico — você não tem como saber se ele existe de \
verdade, e apresentar um lugar fictício como real quebra a confiança do turista.
- NÃO invente preços exatos nem horários de funcionamento — use só as informações \
fornecidas.
- Tom caloroso e direto, sem enrolação. Máximo de ~300 palavras."""


def _formatar_itinerario(paradas: list[dict]) -> str:
    linhas = []
    for i, p in enumerate(paradas, start=1):
        modo = f"chegando de {('carro' if p['modo_chegada'] == 'drive' else 'a pé')}" if p["modo_chegada"] else "início do dia"
        linhas.append(
            f"{i}. {p['nome']} — {modo}, visita das {p['hora_inicio_visita']} às {p['hora_fim_visita']}"
        )
    return "\n".join(linhas)


def narrar_roteiro(paradas: list[dict]) -> str:
    """`paradas`: lista de dicts com nome, modo_chegada, hora_inicio_visita,
    hora_fim_visita (o mesmo formato de `ParadaResponse` da API)."""

    if not paradas:
        return "Nenhuma parada no roteiro para narrar."

    itinerario_texto = _formatar_itinerario(paradas)
    cache_key = f"narrate:{MODEL}:{hashlib.sha256(itinerario_texto.encode('utf-8')).hexdigest()}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached["narrativa"]

    resposta = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Roteiro do dia:\n{itinerario_texto}"},
        ],
        temperature=0.7,
    )
    narrativa = resposta.choices[0].message.content.strip()

    set_cached(cache_key, {"narrativa": narrativa})
    return narrativa
