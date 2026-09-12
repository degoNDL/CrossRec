"""Passo 1 do otimizador: só a ordem, sem janela de horário e sem
encadeamento de modo entre trechos consecutivos — cada trecho escolhe
independentemente o modo mais rápido (ver `CostModel.cost`). Serve de base
antes de acrescentar o resto (`itinerary.py`) e de instância pequena para
provar que o Held-Karp genérico funciona sobre dados reais do Recife.
"""

from dataclasses import dataclass

from optimizer.cost import CostModel
from optimizer.held_karp import held_karp_path, held_karp_path_free_start


@dataclass
class OrdemSimples:
    ordem: list[str]  # ids dos pontos, na ordem de visita
    custo_total_minutos: float


def solve_order(points: list[dict], cost_model: CostModel, start_id: str | None = None) -> OrdemSimples:
    ids = [p["id"] for p in points]
    n = len(ids)
    cost_matrix = [[cost_model.cost(a, b).minutes for b in ids] for a in ids]

    if start_id is not None:
        start_idx = ids.index(start_id)
        path_idx, cost = held_karp_path(cost_matrix, start=start_idx)
    else:
        path_idx, cost = held_karp_path_free_start(cost_matrix)

    return OrdemSimples(ordem=[ids[i] for i in path_idx], custo_total_minutos=cost)
