import json
from types import SimpleNamespace

import pytest

from ai import nl_to_points


CATALOGO = [
    {"id": "marco-zero", "nome": "Marco Zero", "categoria": "historico"},
    {"id": "praia-boa-viagem", "nome": "Praia de Boa Viagem", "categoria": "praia"},
    {"id": "paco-do-frevo", "nome": "Paço do Frevo", "categoria": "museu"},
]


def _fake_response(conteudo: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=conteudo))])


class _FakeClient:
    def __init__(self, conteudo: str):
        self._conteudo = conteudo
        self.chamadas = 0
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.chamadas += 1
        return _fake_response(self._conteudo)


@pytest.fixture(autouse=True)
def limpar_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(nl_to_points, "get_cached", lambda key: None)
    monkeypatch.setattr(nl_to_points, "set_cached", lambda key, value: None)


def test_traduzir_desejo_filtra_ids_validos(monkeypatch):
    fake = _FakeClient(json.dumps({"pontos_ids": ["marco-zero", "praia-boa-viagem"]}))
    monkeypatch.setattr(nl_to_points, "get_client", lambda: fake)

    resultado = nl_to_points.traduzir_desejo("quero centro histórico e praia", CATALOGO)

    assert resultado == ["marco-zero", "praia-boa-viagem"]


def test_traduzir_desejo_descarta_ids_inventados(monkeypatch):
    fake = _FakeClient(json.dumps({"pontos_ids": ["marco-zero", "id-que-nao-existe"]}))
    monkeypatch.setattr(nl_to_points, "get_client", lambda: fake)

    resultado = nl_to_points.traduzir_desejo("qualquer coisa", CATALOGO)

    assert resultado == ["marco-zero"]


def test_traduzir_desejo_lida_com_json_dentro_de_texto_extra(monkeypatch):
    conteudo = 'Aqui está: {"pontos_ids": ["paco-do-frevo"]} espero que ajude!'
    fake = _FakeClient(conteudo)
    monkeypatch.setattr(nl_to_points, "get_client", lambda: fake)

    resultado = nl_to_points.traduzir_desejo("museu de frevo", CATALOGO)

    assert resultado == ["paco-do-frevo"]


def test_traduzir_desejo_resposta_invalida_levanta_erro(monkeypatch):
    fake = _FakeClient("isso não é json nenhum")
    monkeypatch.setattr(nl_to_points, "get_client", lambda: fake)

    with pytest.raises(ValueError):
        nl_to_points.traduzir_desejo("qualquer coisa", CATALOGO)


def test_traduzir_desejo_usa_cache_em_pedidos_repetidos(monkeypatch):
    fake = _FakeClient(json.dumps({"pontos_ids": ["marco-zero"]}))
    monkeypatch.setattr(nl_to_points, "get_client", lambda: fake)

    cache_store: dict = {}
    monkeypatch.setattr(nl_to_points, "get_cached", lambda key: cache_store.get(key))
    monkeypatch.setattr(nl_to_points, "set_cached", lambda key, value: cache_store.__setitem__(key, value))

    nl_to_points.traduzir_desejo("quero ver o marco zero", CATALOGO)
    nl_to_points.traduzir_desejo("quero ver o marco zero", CATALOGO)

    assert fake.chamadas == 1  # segunda chamada veio do cache, não bateu na API
