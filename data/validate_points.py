"""Valida o dataset curado (`curated_points.json`) contra o schema e contra
regras de sanidade geográfica/de negócio do Recife.

Uso:
    python -m data.validate_points
"""

import json
from pathlib import Path

from pydantic import ValidationError

from data.schema import TouristPoint

CURATED_PATH = Path(__file__).parent / "curated_points.json"

# Bounding box aproximado do município do Recife — qualquer ponto fora disso
# é sinal de coordenada errada (ex: lat/lon trocados).
RECIFE_BBOX = {"lat_min": -8.15, "lat_max": -7.95, "lon_min": -35.02, "lon_max": -34.85}


def load_points() -> list[dict]:
    return json.loads(CURATED_PATH.read_text(encoding="utf-8"))


def validate() -> list[TouristPoint]:
    raw_points = load_points()
    errors: list[str] = []
    seen_ids: set[str] = set()
    validated: list[TouristPoint] = []

    for raw in raw_points:
        try:
            point = TouristPoint(**raw)
        except ValidationError as exc:
            errors.append(f"{raw.get('id', '<sem id>')}: schema inválido — {exc}")
            continue

        if point.id in seen_ids:
            errors.append(f"{point.id}: id duplicado")
        seen_ids.add(point.id)

        if not (RECIFE_BBOX["lat_min"] <= point.latitude <= RECIFE_BBOX["lat_max"]):
            errors.append(f"{point.id}: latitude {point.latitude} fora do bbox do Recife")
        if not (RECIFE_BBOX["lon_min"] <= point.longitude <= RECIFE_BBOX["lon_max"]):
            errors.append(f"{point.id}: longitude {point.longitude} fora do bbox do Recife")

        if not point.horario_funcionamento:
            errors.append(f"{point.id}: sem horário de funcionamento definido")

        if point.tempo_visita_sugerido_minutos <= 0:
            errors.append(f"{point.id}: tempo de visita sugerido inválido")

        validated.append(point)

    if errors:
        print(f"{len(errors)} problema(s) encontrado(s):")
        for err in errors:
            print(f"  - {err}")
        raise SystemExit(1)

    print(f"{len(validated)} pontos validados com sucesso.")
    return validated


if __name__ == "__main__":
    validate()
