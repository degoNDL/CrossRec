"""Algoritmo genético para o TSP de caminho — a camada de assinatura do
projeto para quando o problema cresce além do que o Held-Karp exato
consegue resolver em tempo viável (a partir de ~15-18 pontos, onde 2^n já
começa a pesar).

Opera sobre a mesma matriz de custo numérica genérica que `held_karp.py`
(o custo multimodal já combinado por trecho, sem encadeamento de modo —
ver `simple_tsp.py`), o que permite comparar as duas abordagens
diretamente na mesma instância: Held-Karp dá a resposta exata em instâncias
pequenas, o GA precisa convergir para ela; em instâncias grandes, o Held-Karp
não roda e o GA é comparado contra o OR-Tools (ver `benchmark.py`).

Implementação padrão de livro-texto: seleção por torneio, crossover de
ordem (OX), mutação por troca (swap) e elitismo.
"""

import random
from dataclasses import dataclass


@dataclass
class ResultadoGA:
    path: list[int]
    cost: float
    geracoes_executadas: int


def _path_cost(cost_matrix: list[list[float]], path: list[int]) -> float:
    return sum(cost_matrix[path[i]][path[i + 1]] for i in range(len(path) - 1))


def _order_crossover(parent_a: list[int], parent_b: list[int], rng: random.Random) -> list[int]:
    n = len(parent_a)
    i, j = sorted(rng.sample(range(n), 2))
    child = [None] * n
    child[i : j + 1] = parent_a[i : j + 1]
    fill = [gene for gene in parent_b if gene not in child]
    pos = 0
    for k in range(n):
        if child[k] is None:
            child[k] = fill[pos]
            pos += 1
    return child


def _swap_mutation(individual: list[int], rng: random.Random) -> None:
    i, j = rng.sample(range(len(individual)), 2)
    individual[i], individual[j] = individual[j], individual[i]


def _inversion_mutation(individual: list[int], rng: random.Random) -> None:
    """Inverte um trecho contíguo — o operador de mutação que de fato
    funciona bem para TSP (equivalente a um movimento 2-opt aleatório),
    diferente do swap simples que troca só dois genes isolados."""
    i, j = sorted(rng.sample(range(len(individual)), 2))
    individual[i : j + 1] = reversed(individual[i : j + 1])


def _two_opt(cost_matrix: list[list[float]], start: int, individual: list[int], max_passes: int = 6) -> list[int]:
    """Busca local 2-opt sobre o indivíduo (sem contar o nó de início, que
    fica fixo). Aplicada só ao melhor indivíduo de cada geração — é o que
    transforma o GA de "puramente evolutivo" (lento para convergir em TSP)
    em um algoritmo memético, muito mais competitivo contra o OR-Tools.
    """
    path = [start, *individual]
    n = len(path)
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                a, b = path[i - 1], path[i]
                c, d = path[j], path[j + 1]
                delta = (
                    cost_matrix[a][c] + cost_matrix[b][d] - cost_matrix[a][b] - cost_matrix[c][d]
                )
                if delta < -1e-9:
                    path[i : j + 1] = reversed(path[i : j + 1])
                    improved = True
    return path[1:]


def _tournament_select(population: list[list[int]], fitness: list[float], rng: random.Random, k: int = 3) -> list[int]:
    contenders = rng.sample(range(len(population)), k)
    best = min(contenders, key=lambda idx: fitness[idx])
    return population[best]


def solve_ga(
    cost_matrix: list[list[float]],
    start: int = 0,
    population_size: int = 60,
    generations: int = 300,
    mutation_rate: float = 0.15,
    seed: int | None = None,
) -> ResultadoGA:
    n = len(cost_matrix)
    if n <= 2:
        others = [i for i in range(n) if i != start]
        path = [start, *others]
        return ResultadoGA(path=path, cost=_path_cost(cost_matrix, path), geracoes_executadas=0)

    rng = random.Random(seed)
    others = [i for i in range(n) if i != start]

    population = [rng.sample(others, len(others)) for _ in range(population_size)]

    def full_path(individual: list[int]) -> list[int]:
        return [start, *individual]

    best_individual = None
    best_cost = None

    for generation in range(generations):
        fitness = [_path_cost(cost_matrix, full_path(ind)) for ind in population]

        gen_best_idx = min(range(population_size), key=lambda idx: fitness[idx])
        gen_best = _two_opt(cost_matrix, start, population[gen_best_idx])
        gen_best_cost = _path_cost(cost_matrix, full_path(gen_best))

        if best_cost is None or gen_best_cost < best_cost:
            best_cost = gen_best_cost
            best_individual = gen_best[:]

        next_population = [gen_best[:]]  # elitismo (já com refinamento 2-opt)
        while len(next_population) < population_size:
            parent_a = _tournament_select(population, fitness, rng)
            parent_b = _tournament_select(population, fitness, rng)
            child = _order_crossover(parent_a, parent_b, rng)
            if rng.random() < mutation_rate:
                _inversion_mutation(child, rng)
            next_population.append(child)

        population = next_population

    return ResultadoGA(
        path=full_path(best_individual), cost=best_cost, geracoes_executadas=generations
    )
