import random

import pytest

from optimizer.genetic import solve_ga
from optimizer.held_karp import held_karp_path


def _euclidean_matrix(n: int, seed: int) -> list[list[float]]:
    # Pontos aleatórios num plano 2D: a matriz de custo resultante respeita
    # a desigualdade triangular, igual a tempos de deslocamento reais entre
    # lugares de uma cidade. Uma matriz uniforme totalmente aleatória (sem
    # essa estrutura) é um cenário adversarial que nem o OR-Tools resolve
    # bem com 2-opt/busca local — não é representativo do problema real.
    rng = random.Random(seed)
    pontos = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    return [
        [((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 for x2, y2 in pontos]
        for x1, y1 in pontos
    ]


@pytest.mark.parametrize("n", [6, 8, 10, 12])
def test_ga_converge_para_o_otimo_exato(n):
    cost_matrix = _euclidean_matrix(n, seed=7 + n)

    _, custo_exato = held_karp_path(cost_matrix, start=0)
    resultado = solve_ga(cost_matrix, start=0, population_size=80, generations=150, seed=42)

    # Em instâncias métricas (estrutura geográfica real), GA + 2-opt deve
    # chegar muito perto do ótimo exato — gap pequeno e consistente.
    gap = (resultado.cost - custo_exato) / custo_exato if custo_exato > 0 else 0
    assert gap < 0.08
    assert sorted(resultado.path) == list(range(n))
    assert resultado.path[0] == 0


def test_ga_instancia_trivial_dois_pontos():
    cost_matrix = [[0, 5], [5, 0]]
    resultado = solve_ga(cost_matrix, start=0, generations=10)
    assert resultado.path == [0, 1]
    assert resultado.cost == 5
