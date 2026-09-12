import json
from pathlib import Path

import pytest

from optimizer.opening_hours import parse_weekly_schedule, to_hhmm, to_minutes, window_for_weekday

CURATED_POINTS = json.loads(
    (Path(__file__).parent.parent / "data" / "curated_points.json").read_text(encoding="utf-8")
)


def _point(point_id: str) -> dict:
    return next(p for p in CURATED_POINTS if p["id"] == point_id)


def test_todos_os_dias():
    schedule = parse_weekly_schedule({"todos_os_dias": "05:00-22:00"})
    assert all(schedule[day] == ("05:00", "22:00") for day in schedule)


def test_intervalo_de_dois_dias():
    schedule = parse_weekly_schedule({"terca_sexta": "10:00-17:00", "sabado_domingo": "11:00-18:00"})
    assert schedule["segunda"] is None
    assert schedule["terca"] == ("10:00", "17:00")
    assert schedule["sexta"] == ("10:00", "17:00")
    assert schedule["sabado"] == ("11:00", "18:00")
    assert schedule["domingo"] == ("11:00", "18:00")


def test_fechado_explicito():
    schedule = parse_weekly_schedule({"segunda": "fechado", "terca_domingo": "13:00-17:00"})
    assert schedule["segunda"] is None
    assert schedule["terca"] == ("13:00", "17:00")


def test_fecha_dois_dias_forte_cinco_pontas():
    # Caso real: fecha segunda E terça, diferente do padrão "só segunda".
    ponto = _point("forte-cinco-pontas")
    schedule = parse_weekly_schedule(ponto["horario_funcionamento"])
    assert schedule["segunda"] is None
    assert schedule["terca"] is None
    assert schedule["quarta"] == ("10:00", "17:00")
    assert schedule["sabado"] == ("10:00", "16:00")


def test_chave_nao_reconhecida_e_ignorada():
    # "ultima_quinta_do_mes" não é uma regra semanal — não deve quebrar nem
    # sobrescrever a regra normal de quinta-feira (vinda de terca_sexta).
    ponto = _point("museu-cais-do-sertao")
    schedule = parse_weekly_schedule(ponto["horario_funcionamento"])
    assert schedule["quinta"] == ("10:00", "16:00")


def test_janela_partida_e_achatada_para_span_total():
    # capela-dourada: "08:00-11:30 e 14:00-16:00" vira 08:00-16:00.
    ponto = _point("capela-dourada")
    schedule = parse_weekly_schedule(ponto["horario_funcionamento"])
    assert schedule["segunda"] == ("08:00", "16:00")


def test_acesso_livre_24h():
    ponto = _point("marco-zero")
    schedule = parse_weekly_schedule(ponto["horario_funcionamento"])
    assert schedule["quarta"] == ("00:00", "23:59")


def test_window_for_weekday_retorna_minutos():
    ponto = _point("paco-do-frevo")
    window = window_for_weekday(ponto["horario_funcionamento"], "domingo")
    assert window == (11 * 60, 18 * 60)


def test_window_for_weekday_dia_fechado_retorna_none():
    ponto = _point("instituto-ricardo-brennand")
    assert window_for_weekday(ponto["horario_funcionamento"], "segunda") is None


def test_dia_invalido_levanta_erro():
    with pytest.raises(ValueError):
        window_for_weekday({}, "funday")


@pytest.mark.parametrize(
    "hhmm,minutos", [("00:00", 0), ("09:30", 570), ("23:59", 1439), ("13:00", 780)]
)
def test_to_minutes_e_to_hhmm_sao_inversas(hhmm, minutos):
    assert to_minutes(hhmm) == minutos
    assert to_hhmm(minutos) == hhmm
