import itertools
import random

import pytest

from optimizer.held_karp import held_karp_path, held_karp_path_free_start


def brute_force_path(cost_matrix, start=0):
    n = len(cost_matrix)
    others = [i for i in range(n) if i != start]
    best_cost = None
    best_path = None
    for perm in itertools.permutations(others):
        path = [start, *perm]
        cost = sum(cost_matrix[path[i]][path[i + 1]] for i in range(n - 1))
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_path = path
    return best_path, best_cost


def test_instancia_conhecida_linha_reta():
    # Quatro pontos em linha (0,1,2,3): o caminho ótimo partindo de 0 é
    # visitar em ordem, custo = soma dos trechos consecutivos.
    cost_matrix = [
        [0, 1, 2, 3],
        [1, 0, 1, 2],
        [2, 1, 0, 1],
        [3, 2, 1, 0],
    ]
    path, cost = held_karp_path(cost_matrix, start=0)
    assert path == [0, 1, 2, 3]
    assert cost == 3


def test_instancia_conhecida_desvio_vale_a_pena():
    # A ordem "natural" 0-1-2 é pior que pular para 2 primeiro.
    cost_matrix = [
        [0, 10, 1],
        [10, 0, 10],
        [1, 10, 0],
    ]
    path, cost = held_karp_path(cost_matrix, start=0)
    assert path == [0, 2, 1]
    assert cost == 11


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7])
def test_bate_com_forca_bruta(n):
    random.seed(42 + n)
    cost_matrix = [[random.uniform(1, 100) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        cost_matrix[i][i] = 0

    expected_path, expected_cost = brute_force_path(cost_matrix, start=0)
    path, cost = held_karp_path(cost_matrix, start=0)

    assert path[0] == 0
    assert sorted(path) == list(range(n))
    assert cost == pytest.approx(expected_cost)
    assert cost == pytest.approx(
        sum(cost_matrix[path[i]][path[i + 1]] for i in range(n - 1))
    )


def test_free_start_encontra_melhor_inicio_possivel():
    # Ponto 1 no meio é claramente o melhor início (evita o trecho caro 0-2).
    cost_matrix = [
        [0, 1, 100],
        [1, 0, 1],
        [100, 1, 0],
    ]
    path, cost = held_karp_path_free_start(cost_matrix)
    assert path[0] == 0 or path[0] == 2  # começar em qualquer ponta é ótimo
    assert cost == 2


def test_caminho_com_um_unico_ponto():
    path, cost = held_karp_path([[0]], start=0)
    assert path == [0]
    assert cost == 0.0
