"""Compara as três abordagens do otimizador na mesma instância (mesma
matriz de custo, mesmo ponto de partida):

1. Held-Karp (exato) — só roda até ~n=12, referência de corretude/ótimo.
2. Algoritmo genético (`optimizer/genetic.py`) — a camada de assinatura.
3. OR-Tools (`ortools.constraint_solver`) — solver de referência da
   indústria, usado aqui só para benchmark, não como parte do produto.

Em instâncias pequenas, o GA deve empatar (ou quase) com o Held-Karp
exato. Em instâncias grandes, onde o Held-Karp não é viável (2^n explode),
o GA é comparado contra o OR-Tools em qualidade de solução e tempo de
execução — essa comparação é o principal diferencial técnico do projeto
para o currículo.

Uso:
    python -m optimizer.benchmark
"""

import random
import time

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from optimizer.genetic import solve_ga
from optimizer.held_karp import held_karp_path


def _random_matrix(n: int, seed: int) -> list[list[float]]:
    # Pontos aleatórios num plano 2D (distância euclidiana) em vez de
    # custos totalmente aleatórios: respeita a desigualdade triangular,
    # como tempos de deslocamento reais numa cidade — o cenário que o
    # GA (via 2-opt) e o OR-Tools são de fato desenhados para resolver bem.
    # Uma matriz sem essa estrutura é um teste adversarial artificial que
    # não representa o problema real do CrossRec.
    rng = random.Random(seed)
    pontos = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    return [
        [((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 for x2, y2 in pontos]
        for x1, y1 in pontos
    ]


def _solve_with_ortools(cost_matrix: list[list[float]], start: int) -> tuple[list[int], float]:
    n = len(cost_matrix)
    # OR-Tools resolve ciclos por padrão; simulamos um caminho (sem voltar
    # ao início) adicionando um nó "fantasma" de custo zero para/de todos
    # os outros — o tour ótimo do ciclo fantasma-incluído corresponde ao
    # caminho ótimo real quando removemos o fantasma da solução.
    ghost = n
    size = n + 1
    scale = 1000  # OR-Tools trabalha com custos inteiros

    def scaled_cost(i, j):
        if i == ghost or j == ghost:
            return 0
        return int(round(cost_matrix[i][j] * scale))

    manager = pywrapcp.RoutingIndexManager(size, 1, [start], [ghost])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return scaled_cost(from_node, to_node)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(5)

    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        raise RuntimeError("OR-Tools não encontrou solução.")

    index = routing.Start(0)
    path = []
    total_scaled = 0
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != ghost:
            path.append(node)
        next_index = solution.Value(routing.NextVar(index))
        if node != ghost and manager.IndexToNode(next_index) != ghost:
            total_scaled += scaled_cost(node, manager.IndexToNode(next_index))
        index = next_index

    return path, total_scaled / scale


def benchmark_pequena_escala():
    print("=== Held-Karp (exato) vs GA — instâncias pequenas (n<=12) ===")
    print(f"{'n':>3} | {'custo exato':>12} | {'custo GA':>10} | {'gap':>7} | {'t. exato':>9} | {'t. GA':>9}")
    for n in (6, 8, 10, 12):
        matrix = _random_matrix(n, seed=100 + n)

        t0 = time.perf_counter()
        _, custo_exato = held_karp_path(matrix, start=0)
        t_exato = time.perf_counter() - t0

        t0 = time.perf_counter()
        resultado_ga = solve_ga(matrix, start=0, population_size=100, generations=300, seed=1)
        t_ga = time.perf_counter() - t0

        gap = (resultado_ga.cost - custo_exato) / custo_exato * 100 if custo_exato > 0 else 0
        print(
            f"{n:>3} | {custo_exato:>12.1f} | {resultado_ga.cost:>10.1f} | "
            f"{gap:>6.1f}% | {t_exato:>8.3f}s | {t_ga:>8.3f}s"
        )


def benchmark_grande_escala():
    print()
    print("=== GA vs OR-Tools — instâncias grandes (Held-Karp inviável aqui) ===")
    print(f"{'n':>4} | {'custo GA':>10} | {'custo OR-Tools':>14} | {'gap':>7} | {'t. GA':>9} | {'t. OR-Tools':>12}")
    for n in (20, 40, 60):
        matrix = _random_matrix(n, seed=200 + n)

        t0 = time.perf_counter()
        resultado_ga = solve_ga(matrix, start=0, population_size=150, generations=400, seed=1)
        t_ga = time.perf_counter() - t0

        t0 = time.perf_counter()
        _, custo_ortools = _solve_with_ortools(matrix, start=0)
        t_ortools = time.perf_counter() - t0

        gap = (
            (resultado_ga.cost - custo_ortools) / custo_ortools * 100 if custo_ortools > 0 else 0
        )
        print(
            f"{n:>4} | {resultado_ga.cost:>10.1f} | {custo_ortools:>14.1f} | "
            f"{gap:>6.1f}% | {t_ga:>8.3f}s | {t_ortools:>11.3f}s"
        )


if __name__ == "__main__":
    benchmark_pequena_escala()
    benchmark_grande_escala()
