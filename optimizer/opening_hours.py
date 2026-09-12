"""Converte o `horario_funcionamento` semi-livre de `curated_points.json`
(ex: {"terca_domingo": "13:00-17:00"}) num horário semanal estruturado que o
otimizador consegue consultar por dia da semana.

Limitações conhecidas e assumidas de propósito (documentadas para não
mascarar imprecisão como exatidão):
- Quando um dia tem dois intervalos de horário (ex: capela-dourada, que
  fecha para almoço), a janela é achatada para [primeiro início, último
  fim] — mais permissivo que a realidade. Aceitável para o MVP; modelar
  intervalos partidos exigiria um segundo nível no DP do otimizador.
- Chaves que não são um dia nem um intervalo de dois dias reconhecidos (ex:
  "ultima_quinta_do_mes") são ignoradas — são exceções pontuais, não regra
  semanal.
"""

import re

WEEKDAYS_PT = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

_TIME_RANGE_RE = re.compile(r"(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})")

WeeklySchedule = dict[str, tuple[str, str] | None]


def to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def to_hhmm(minutes: float) -> str:
    minutes = int(round(minutes))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _resolve_days(key: str) -> list[str] | None:
    if key == "todos_os_dias":
        return list(WEEKDAYS_PT)

    tokens = key.split("_")
    if len(tokens) == 1 and tokens[0] in WEEKDAYS_PT:
        return [tokens[0]]
    if len(tokens) == 2 and tokens[0] in WEEKDAYS_PT and tokens[1] in WEEKDAYS_PT:
        start_idx = WEEKDAYS_PT.index(tokens[0])
        end_idx = WEEKDAYS_PT.index(tokens[1])
        if start_idx <= end_idx:
            return WEEKDAYS_PT[start_idx : end_idx + 1]
    return None  # chave não reconhecida — ignorada de propósito


def parse_weekly_schedule(horario_funcionamento: dict[str, str]) -> WeeklySchedule:
    schedule: WeeklySchedule = {day: None for day in WEEKDAYS_PT}

    for key, value in horario_funcionamento.items():
        days = _resolve_days(key)
        if days is None:
            continue

        value_lower = value.lower()
        if "fechado" in value_lower:
            continue  # já é None por padrão

        matches = _TIME_RANGE_RE.findall(value)
        if matches:
            starts = [f"{h.zfill(2)}:{m}" for h, m, _, _ in matches]
            ends = [f"{h2.zfill(2)}:{m2}" for _, _, h2, m2 in matches]
            window = (min(starts), max(ends))
        elif "24h" in value_lower or "livre" in value_lower:
            window = ("00:00", "23:59")
        else:
            continue  # não confirmado — permanece fechado por padrão (conservador)

        for day in days:
            schedule[day] = window

    return schedule


def window_for_weekday(
    horario_funcionamento: dict[str, str], weekday: str
) -> tuple[int, int] | None:
    """Janela do dia em minutos desde a meia-noite, ou None se fechado."""

    if weekday not in WEEKDAYS_PT:
        raise ValueError(f"Dia da semana inválido: '{weekday}'. Use um de {WEEKDAYS_PT}.")

    schedule = parse_weekly_schedule(horario_funcionamento)
    window = schedule[weekday]
    if window is None:
        return None
    return to_minutes(window[0]), to_minutes(window[1])
