from types import SimpleNamespace

import pytest

from ai import narrate


def _fake_response(conteudo: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=conteudo))])


class _FakeClient:
    def __init__(self, conteudo: str):
        self._conteudo = conteudo
        self.chamadas = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamadas += 1
        return _fake_response(self._conteudo)


PARADAS = [
    {
        "nome": "Marco Zero",
        "modo_chegada": None,
        "hora_inicio_visita": "09:00",
        "hora_fim_visita": "09:20",
    },
    {
        "nome": "Mercado de São José",
        "modo_chegada": "drive",
        "hora_inicio_visita": "09:30",
        "hora_fim_visita": "10:15",
    },
]


@pytest.fixture(autouse=True)
def limpar_cache(monkeypatch):
    monkeypatch.setattr(narrate, "get_cached", lambda key: None)
    monkeypatch.setattr(narrate, "set_cached", lambda key, value: None)


def test_narrar_roteiro_retorna_texto_do_llm(monkeypatch):
    fake = _FakeClient("Comece o dia no Marco Zero, o coração do Recife...")
    monkeypatch.setattr(narrate, "get_client", lambda: fake)

    resultado = narrate.narrar_roteiro(PARADAS)

    assert "Marco Zero" in resultado
    assert fake.chamadas == 1


def test_narrar_roteiro_lista_vazia_nao_chama_llm(monkeypatch):
    fake = _FakeClient("não deveria ser chamado")
    monkeypatch.setattr(narrate, "get_client", lambda: fake)

    resultado = narrate.narrar_roteiro([])

    assert fake.chamadas == 0
    assert "roteiro" in resultado.lower()


def test_narrar_roteiro_usa_cache(monkeypatch):
    fake = _FakeClient("texto narrado")
    monkeypatch.setattr(narrate, "get_client", lambda: fake)

    cache_store: dict = {}
    monkeypatch.setattr(narrate, "get_cached", lambda key: cache_store.get(key))
    monkeypatch.setattr(narrate, "set_cached", lambda key, value: cache_store.__setitem__(key, value))

    narrate.narrar_roteiro(PARADAS)
    narrate.narrar_roteiro(PARADAS)

    assert fake.chamadas == 1
