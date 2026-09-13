import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_listar_pontos(client):
    resposta = client.get("/pontos")
    assert resposta.status_code == 200
    pontos = resposta.json()
    assert len(pontos) == 15
    assert {"id", "nome", "latitude", "longitude", "categoria"} <= pontos[0].keys()


def test_calcular_roteiro_valido(client):
    resposta = client.post(
        "/roteiro",
        json={
            "pontos_ids": ["marco-zero", "paco-do-frevo", "mercado-sao-jose"],
            "dia_semana": "quinta",
            "hora_inicio_dia": "09:00",
            "hora_fim_dia": "18:00",
        },
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["completo"] is True
    assert len(corpo["paradas"]) == 3
    assert {p["ponto_id"] for p in corpo["paradas"]} == {"marco-zero", "paco-do-frevo", "mercado-sao-jose"}
    assert corpo["paradas"][0]["nome"]  # nome do ponto veio junto, não só o id


def test_calcular_roteiro_com_inicio_fixo(client):
    resposta = client.post(
        "/roteiro",
        json={
            "pontos_ids": ["marco-zero", "paco-do-frevo"],
            "dia_semana": "quinta",
            "ponto_inicio_id": "paco-do-frevo",
        },
    )
    assert resposta.status_code == 200
    assert resposta.json()["paradas"][0]["ponto_id"] == "paco-do-frevo"


def test_ponto_inexistente_retorna_404(client):
    resposta = client.post(
        "/roteiro",
        json={"pontos_ids": ["marco-zero", "ponto-que-nao-existe"], "dia_semana": "quinta"},
    )
    assert resposta.status_code == 404
    assert "ponto-que-nao-existe" in resposta.json()["detail"]


def test_dia_semana_invalido_retorna_422(client):
    resposta = client.post(
        "/roteiro", json={"pontos_ids": ["marco-zero"], "dia_semana": "domsday"}
    )
    assert resposta.status_code == 422


def test_ids_duplicados_retorna_422(client):
    resposta = client.post(
        "/roteiro",
        json={"pontos_ids": ["marco-zero", "marco-zero"], "dia_semana": "quinta"},
    )
    assert resposta.status_code == 422


def test_lista_vazia_retorna_422(client):
    resposta = client.post("/roteiro", json={"pontos_ids": [], "dia_semana": "quinta"})
    assert resposta.status_code == 422


def test_mais_de_15_pontos_retorna_422(client):
    resposta = client.post(
        "/roteiro",
        json={"pontos_ids": [f"ponto-{i}" for i in range(16)], "dia_semana": "quinta"},
    )
    assert resposta.status_code == 422


def test_hora_fim_antes_do_inicio_retorna_422(client):
    resposta = client.post(
        "/roteiro",
        json={
            "pontos_ids": ["marco-zero"],
            "dia_semana": "quinta",
            "hora_inicio_dia": "18:00",
            "hora_fim_dia": "09:00",
        },
    )
    assert resposta.status_code == 422


def test_hora_mal_formatada_retorna_422(client):
    resposta = client.post(
        "/roteiro",
        json={"pontos_ids": ["marco-zero"], "dia_semana": "quinta", "hora_inicio_dia": "9h"},
    )
    assert resposta.status_code == 422


def test_ponto_inicio_fora_da_lista_retorna_422(client):
    resposta = client.post(
        "/roteiro",
        json={
            "pontos_ids": ["marco-zero", "paco-do-frevo"],
            "dia_semana": "quinta",
            "ponto_inicio_id": "mercado-sao-jose",
        },
    )
    assert resposta.status_code == 422


def test_interpretar_traduz_texto_para_ids(client, monkeypatch):
    monkeypatch.setattr(api_main, "traduzir_desejo", lambda texto, catalogo: ["marco-zero"])

    resposta = client.post("/interpretar", json={"texto": "quero ver o centro histórico"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["pontos_ids"] == ["marco-zero"]
    assert corpo["pontos"][0]["id"] == "marco-zero"


def test_interpretar_texto_curto_retorna_422(client):
    resposta = client.post("/interpretar", json={"texto": "oi"})
    assert resposta.status_code == 422


def test_interpretar_falha_da_ia_retorna_502(client, monkeypatch):
    def _quebra(texto, catalogo):
        raise RuntimeError("Groq indisponível")

    monkeypatch.setattr(api_main, "traduzir_desejo", _quebra)

    resposta = client.post("/interpretar", json={"texto": "quero ver o centro histórico"})

    assert resposta.status_code == 502


def test_roteiro_com_narracao(client, monkeypatch):
    monkeypatch.setattr(api_main, "narrar_roteiro", lambda paradas: "Um dia incrível no Recife!")

    resposta = client.post(
        "/roteiro",
        json={"pontos_ids": ["marco-zero", "paco-do-frevo"], "dia_semana": "quinta", "narrar": True},
    )

    assert resposta.status_code == 200
    assert resposta.json()["narrativa"] == "Um dia incrível no Recife!"


def test_roteiro_sem_narracao_nao_chama_ia(client, monkeypatch):
    chamou = {"sim": False}

    def _marca(paradas):
        chamou["sim"] = True
        return "não deveria ser chamado"

    monkeypatch.setattr(api_main, "narrar_roteiro", _marca)

    resposta = client.post(
        "/roteiro", json={"pontos_ids": ["marco-zero"], "dia_semana": "quinta", "narrar": False}
    )

    assert resposta.status_code == 200
    assert resposta.json()["narrativa"] is None
    assert chamou["sim"] is False


def test_roteiro_falha_na_narracao_nao_derruba_a_requisicao(client, monkeypatch):
    def _quebra(paradas):
        raise RuntimeError("Groq indisponível")

    monkeypatch.setattr(api_main, "narrar_roteiro", _quebra)

    resposta = client.post(
        "/roteiro",
        json={"pontos_ids": ["marco-zero"], "dia_semana": "quinta", "narrar": True},
    )

    assert resposta.status_code == 200
    assert resposta.json()["narrativa"] is None


def test_ponto_fechado_no_dia_aparece_em_ignorados(client):
    resposta = client.post(
        "/roteiro",
        json={
            "pontos_ids": ["marco-zero", "sinagoga-kahal-zur-israel"],
            "dia_semana": "sabado",  # sinagoga fecha aos sábados
        },
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert "sinagoga-kahal-zur-israel" in corpo["pontos_ignorados_fechados"]
