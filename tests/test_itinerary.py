from optimizer.cost import CostModel
from optimizer.itinerary import solve

AMPLO = {"todos_os_dias": "00:00-23:59"}


def _ponto(id_, horario=AMPLO, duracao=0):
    return {"id": id_, "horario_funcionamento": horario, "tempo_visita_sugerido_minutos": duracao}


def test_penalidade_de_troca_nao_e_cobrada_duas_vezes_ao_continuar_de_carro():
    # A->B e B->C são muito mais rápidos de carro; a pé é proibitivo. Se a
    # penalidade fosse cobrada em CADA trecho de carro (modelo ingênuo do
    # passo 1), o custo seria (5+6)+(5+6)=22. Encadeando o modo, dirigir os
    # dois trechos seguidos paga a penalidade só na primeira troca: 5+6+5=16.
    walk_matrix = {
        "a": {"a": 0, "b": 100, "c": 100},
        "b": {"a": 100, "b": 0, "c": 100},
        "c": {"a": 100, "b": 100, "c": 0},
    }
    drive_matrix = {
        "a": {"a": 0, "b": 5, "c": 12},
        "b": {"a": 5, "b": 0, "c": 5},
        "c": {"a": 12, "b": 5, "c": 0},
    }
    model = CostModel(walk_matrix, drive_matrix)
    points = [_ponto("a"), _ponto("b"), _ponto("c")]

    itinerario = solve(points, model, weekday="terca", start_id="a")

    assert itinerario.completo
    assert [p.ponto_id for p in itinerario.paradas] == ["a", "b", "c"]
    assert itinerario.paradas[1].modo_chegada == "drive"
    assert itinerario.paradas[2].modo_chegada == "drive"
    assert itinerario.custo_total_minutos == 16.0


def test_trecho_curto_ainda_prefere_caminhada():
    walk_matrix = {"a": {"a": 0, "b": 5}, "b": {"a": 5, "b": 0}}
    drive_matrix = {"a": {"a": 0, "b": 10}, "b": {"a": 10, "b": 0}}
    model = CostModel(walk_matrix, drive_matrix)
    points = [_ponto("a"), _ponto("b")]

    itinerario = solve(points, model, weekday="terca", start_id="a")

    assert itinerario.paradas[1].modo_chegada == "walk"
    assert itinerario.custo_total_minutos == 5.0


def test_ponto_fechado_no_dia_e_ignorado():
    walk_matrix = {"a": {"a": 0, "b": 5}, "b": {"a": 5, "b": 0}}
    drive_matrix = {"a": {"a": 0, "b": 10}, "b": {"a": 10, "b": 0}}
    model = CostModel(walk_matrix, drive_matrix)
    points = [_ponto("a"), _ponto("b", horario={"segunda": "fechado", "terca_domingo": "09:00-17:00"})]

    itinerario = solve(points, model, weekday="segunda", start_id="a")

    assert [p.ponto_id for p in itinerario.paradas] == ["a"]
    assert itinerario.pontos_ignorados_fechados == ["b"]
    assert itinerario.completo  # "completo" entre os candidatos abertos naquele dia


def test_espera_quando_chega_antes_de_abrir():
    walk_matrix = {"a": {"a": 0, "b": 5}, "b": {"a": 5, "b": 0}}
    drive_matrix = {"a": {"a": 0, "b": 10}, "b": {"a": 10, "b": 0}}
    model = CostModel(walk_matrix, drive_matrix)
    # b só abre às 10:00; chegando às 09:05 (09:00 + 5min a pé) tem que esperar.
    points = [_ponto("a"), _ponto("b", horario={"todos_os_dias": "10:00-18:00"})]

    itinerario = solve(points, model, weekday="terca", start_id="a", hora_inicio_dia="09:00")

    assert itinerario.paradas[1].hora_chegada == "09:05"
    assert itinerario.paradas[1].hora_inicio_visita == "10:00"
    assert itinerario.paradas[1].espera_minutos == 55.0


def test_orienteering_quando_nao_cabe_tudo_no_dia():
    # 3 pontos a 30 min de carro um do outro, 20 min de visita cada.
    # a (540-560) -> b (596-616, com 6min de penalidade na 1a troca p/
    # carro) cabe num dia até 10:20 (620min). O 3o ponto (c) só terminaria
    # às 666min (30min a mais de carro, sem nova penalidade pois já estava
    # dirigindo) — estoura o orçamento. Orienteering deve parar em 2 pontos.
    ids = ["a", "b", "c"]
    walk_matrix = {i: {j: 999 for j in ids} for i in ids}
    for i in ids:
        walk_matrix[i][i] = 0
    drive_matrix = {i: {j: 30 for j in ids} for i in ids}
    for i in ids:
        drive_matrix[i][i] = 0
    model = CostModel(walk_matrix, drive_matrix)
    points = [_ponto(i, duracao=20) for i in ids]

    itinerario = solve(
        points, model, weekday="terca", start_id="a", hora_inicio_dia="09:00", hora_fim_dia="10:20"
    )

    assert not itinerario.completo
    assert len(itinerario.paradas) == 2
    assert itinerario.paradas[0].ponto_id == "a"
