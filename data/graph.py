"""Download e cache do grafo de ruas do Recife via OSMnx.

Duas redes são baixadas porque servem propósitos diferentes: a de caminhada
inclui calçadões e vias de pedestre que não servem para carro, e a de carro
inclui vias expressas que não servem para pedestre. Usar uma única rede para
os dois modos geraria rotas irreais (ex: mandar o turista andar pela BR-101).

Os grafos ficam em CRS geográfico (EPSG:4326, lat/lon), que é o que o OSMnx
usa por padrão. Isso é suficiente aqui porque o OSMnx já calcula o atributo
`length` de cada aresta em metros (distância geodésica) no momento da
construção do grafo — não precisamos reprojetar para UTM só para obter
tempo de deslocamento via caminho mínimo. Reprojeção só seria necessária
para operações geométricas de área/buffer, que este projeto não usa.
"""

from pathlib import Path

import networkx as nx
import osmnx as ox

PLACE = "Recife, Pernambuco, Brazil"
CACHE_DIR = Path(__file__).parent / "cache"
WALK_GRAPH_PATH = CACHE_DIR / "recife_walk.graphml"
DRIVE_GRAPH_PATH = CACHE_DIR / "recife_drive.graphml"

# Velocidade média de caminhada de um turista (km/h) — usada para converter
# distância em tempo na rede de pedestre, que não tem tag de velocidade.
WALK_SPEED_KMH = 4.5

# Velocidade de carro por classe viária (km/h), usada quando a via não tem
# tag `maxspeed` no OSM (a maioria das vias locais não tem). O portal de
# dados abertos do Recife (dados.recife.pe.gov.br) não publica um dataset de
# limite de velocidade por segmento de via — só contagem de veículos por
# faixa de velocidade em pontos fixos de radar/lombada, que não cobre a
# malha completa e não é um mapa de velocidades. Por isso os valores abaixo
# seguem a classificação de velocidade por tipo de via do Código de Trânsito
# Brasileiro (Art. 61): via de trânsito rápido 80, arterial 60, coletora 40,
# local 30. É o proxy realista padrão em roteamento quando falta maxspeed
# por segmento (mesma lógica que o OSMnx usa como fallback).
HWY_SPEEDS_KMH = {
    "motorway": 80,
    "motorway_link": 80,
    "trunk": 80,
    "trunk_link": 80,
    "primary": 60,
    "primary_link": 60,
    "secondary": 40,
    "secondary_link": 40,
    "tertiary": 40,
    "tertiary_link": 40,
    "residential": 30,
    "unclassified": 30,
    "living_street": 20,
    "service": 20,
}


def _load_or_build(path: Path, network_type: str) -> nx.MultiDiGraph:
    if path.exists():
        return ox.load_graphml(path)

    graph = ox.graph_from_place(PLACE, network_type=network_type, simplify=True)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(graph, path)
    return graph


def get_walk_graph() -> nx.MultiDiGraph:
    graph = _load_or_build(WALK_GRAPH_PATH, "walk")
    for _, _, data in graph.edges(data=True):
        length_m = data["length"]
        data["travel_time"] = length_m / (WALK_SPEED_KMH * 1000 / 3600)
    return graph


def get_drive_graph(hwy_speeds: dict[str, float] | None = None) -> nx.MultiDiGraph:
    graph = _load_or_build(DRIVE_GRAPH_PATH, "drive")
    # Preenche velocidade por via: usa a tag `maxspeed` do OSM quando existe;
    # onde falta (maioria das vias locais), imputa por `hwy_speeds` (tabela
    # do CTB por classe viária, ver acima) — comportamento padrão do OSMnx.
    graph = ox.routing.add_edge_speeds(graph, hwy_speeds=hwy_speeds or HWY_SPEEDS_KMH)
    graph = ox.routing.add_edge_travel_times(graph)
    return graph


if __name__ == "__main__":
    walk = get_walk_graph()
    drive = get_drive_graph()
    print(f"Grafo de caminhada: {len(walk.nodes)} nós, {len(walk.edges)} arestas")
    print(f"Grafo de carro: {len(drive.nodes)} nós, {len(drive.edges)} arestas")
