"""Coleta bruta de pontos turísticos do Recife via Overpass API (OpenStreetMap).

Este script NÃO é a fonte de verdade do dataset do MVP — o OSM tem cobertura
e qualidade variáveis. Ele serve para (a) ter uma base ampla para explorar
candidatos futuros e (b) cross-checar coordenadas dos pontos curados
manualmente em `curated_points.json`.

Uso:
    python -m data.collect_overpass
"""

import json
from pathlib import Path

import requests

OVERPASS_URL = "https://lz4.overpass-api.de/api/interpreter"
RAW_OUTPUT_PATH = Path(__file__).parent / "raw" / "osm_points.json"

# Categorias que interessam para pontos turísticos: atrações, museus e
# pontos históricos. Usa bbox direto (em vez de resolver a área administrativa
# do Recife) porque a resolução de área é pesada nos servidores públicos do
# Overpass e costuma estourar timeout; o bbox cobre o núcleo turístico da
# cidade (centro histórico, Boa Viagem) e é suficiente para exploração.
RECIFE_BBOX = "-8.13,-34.95,-8.02,-34.85"  # south,west,north,east
OVERPASS_QUERY = f"""
[out:json][timeout:50];
(
  node["tourism"~"attraction|museum|artwork|viewpoint"]({RECIFE_BBOX});
  way["tourism"~"attraction|museum|artwork|viewpoint"]({RECIFE_BBOX});
  node["historic"]({RECIFE_BBOX});
  way["historic"]({RECIFE_BBOX});
);
out center tags;
"""


def collect() -> list[dict]:
    headers = {"User-Agent": "CrossRec/0.1 (projeto de portfolio; contato: diegoclebson32@gmail.com)"}
    response = requests.post(
        OVERPASS_URL, data={"data": OVERPASS_QUERY}, headers=headers, timeout=120
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])

    points = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # sem nome não é utilizável para o turista

        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue

        points.append(
            {
                "osm_id": el["id"],
                "osm_type": el["type"],
                "nome": name,
                "latitude": lat,
                "longitude": lon,
                "tourism": tags.get("tourism"),
                "historic": tags.get("historic"),
                "opening_hours_osm": tags.get("opening_hours"),
                "raw_tags": tags,
            }
        )
    return points


def main() -> None:
    points = collect()
    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUTPUT_PATH.write_text(
        json.dumps(points, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(points)} pontos brutos salvos em {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
