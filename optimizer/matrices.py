"""Matrizes de tempo de deslocamento (em minutos) entre todos os pontos
turísticos curados, uma para caminhada e outra para carro.

As matrizes são cacheadas em disco porque reconstruir o grafo e recalcular
todos os caminhos mínimos a cada requisição é caro (minutos, não
milissegundos) — o cache é o que torna a API (Fase 4) viável.
"""

import json
from pathlib import Path

import networkx as nx
import osmnx as ox

from data.graph import get_drive_graph, get_walk_graph

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
WALK_MATRIX_PATH = CACHE_DIR / "matrix_walk.json"
DRIVE_MATRIX_PATH = CACHE_DIR / "matrix_drive.json"

CURATED_POINTS_PATH = Path(__file__).parent.parent / "data" / "curated_points.json"


def load_points() -> list[dict]:
    return json.loads(CURATED_POINTS_PATH.read_text(encoding="utf-8"))


def _build_matrix(graph: nx.MultiDiGraph, points: list[dict]) -> dict[str, dict[str, float | None]]:
    """Tempo de deslocamento em minutos entre cada par de pontos, seguindo a
    rede real de ruas (não linha reta). `None` quando não há caminho na rede
    (ex: ponto isolado do grafo de carro)."""

    lats = [p["latitude"] for p in points]
    lons = [p["longitude"] for p in points]
    nearest = ox.distance.nearest_nodes(graph, X=lons, Y=lats)
    node_by_point_id = {p["id"]: node for p, node in zip(points, nearest)}

    matrix: dict[str, dict[str, float | None]] = {}
    for origin in points:
        origin_node = node_by_point_id[origin["id"]]
        lengths = nx.single_source_dijkstra_path_length(graph, origin_node, weight="travel_time")
        matrix[origin["id"]] = {}
        for dest in points:
            if dest["id"] == origin["id"]:
                matrix[origin["id"]][dest["id"]] = 0.0
                continue
            dest_node = node_by_point_id[dest["id"]]
            seconds = lengths.get(dest_node)
            matrix[origin["id"]][dest["id"]] = seconds / 60 if seconds is not None else None
    return matrix


def build_all_matrices(force: bool = False) -> tuple[dict, dict]:
    points = load_points()

    if not force and WALK_MATRIX_PATH.exists() and DRIVE_MATRIX_PATH.exists():
        walk_matrix = json.loads(WALK_MATRIX_PATH.read_text(encoding="utf-8"))
        drive_matrix = json.loads(DRIVE_MATRIX_PATH.read_text(encoding="utf-8"))
        return walk_matrix, drive_matrix

    walk_matrix = _build_matrix(get_walk_graph(), points)
    drive_matrix = _build_matrix(get_drive_graph(), points)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    WALK_MATRIX_PATH.write_text(json.dumps(walk_matrix, indent=2), encoding="utf-8")
    DRIVE_MATRIX_PATH.write_text(json.dumps(drive_matrix, indent=2), encoding="utf-8")

    return walk_matrix, drive_matrix


if __name__ == "__main__":
    walk_matrix, drive_matrix = build_all_matrices(force=True)
    n = len(walk_matrix)
    print(f"Matrizes {n}x{n} construídas e cacheadas em {CACHE_DIR}")
