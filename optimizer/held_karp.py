"""Held-Karp clássico: TSP de caminho (não voláutica a fechar ciclo) por
programação dinâmica sobre bitmask, com início fixo.

Esta é a implementação de referência mencionada no roadmap ("testar com
instâncias pequenas de resposta conhecida, para provar que a solução é de
fato correta antes de seguir"). Opera sobre uma matriz de custo numérica
genérica (não sabe nada sobre pontos turísticos, modos de transporte ou
janelas de horário) — é o alicerce que os módulos `itinerary.py` e
`genetic.py` usam como referência de corretude nos testes.

Complexidade: O(2^n * n^2) tempo, O(2^n * n) espaço. Viável para n até ~15.
"""


def held_karp_path(cost_matrix: list[list[float]], start: int = 0) -> tuple[list[int], float]:
    """Retorna (ordem_de_indices, custo_total) do caminho de custo mínimo que
    visita todos os índices de `cost_matrix` exatamente uma vez, começando em
    `start`. Não retorna ao início (é um caminho, não um ciclo)."""

    n = len(cost_matrix)
    if n == 0:
        return [], 0.0
    if n == 1:
        return [start], 0.0

    full_mask = (1 << n) - 1
    start_bit = 1 << start

    # dp[(mask, j)] = custo mínimo para visitar exatamente os índices de
    # `mask` (que sempre inclui `start`), terminando em j.
    dp: dict[tuple[int, int], float] = {(start_bit, start): 0.0}
    parent: dict[tuple[int, int], int] = {}

    for mask in range(1, full_mask + 1):
        if not (mask & start_bit):
            continue
        for j in range(n):
            if not (mask & (1 << j)):
                continue
            if j == start and mask != start_bit:
                continue  # o início só aparece sozinho no estado inicial
            key = (mask, j)
            if key in dp:
                continue

            prev_mask = mask & ~(1 << j)
            best_cost = None
            best_k = None
            for k in range(n):
                if k == j or not (prev_mask & (1 << k)):
                    continue
                prev_key = (prev_mask, k)
                if prev_key not in dp:
                    continue
                candidate = dp[prev_key] + cost_matrix[k][j]
                if best_cost is None or candidate < best_cost:
                    best_cost = candidate
                    best_k = k

            if best_cost is not None:
                dp[key] = best_cost
                parent[key] = best_k

    best_end_cost = None
    best_end = None
    for j in range(n):
        if j == start:
            continue
        key = (full_mask, j)
        if key in dp and (best_end_cost is None or dp[key] < best_end_cost):
            best_end_cost = dp[key]
            best_end = j

    if best_end is None:
        raise ValueError("Não há caminho que visite todos os pontos a partir de 'start'.")

    path = []
    mask, j = full_mask, best_end
    while (mask, j) != (start_bit, start):
        path.append(j)
        k = parent[(mask, j)]
        mask = mask & ~(1 << j)
        j = k
    path.append(start)
    path.reverse()

    return path, best_end_cost


def held_karp_path_free_start(cost_matrix: list[list[float]]) -> tuple[list[int], float]:
    """Como `held_karp_path`, mas tenta todos os pontos de partida possíveis
    e retorna o melhor. Útil quando o turista não tem um ponto fixo de
    início. Custo adicional de fator n — ainda trivial para n pequeno."""

    n = len(cost_matrix)
    if n <= 1:
        return held_karp_path(cost_matrix, start=0)

    best_path, best_cost = None, None
    for start in range(n):
        path, cost = held_karp_path(cost_matrix, start=start)
        if best_cost is None or cost < best_cost:
            best_path, best_cost = path, cost
    return best_path, best_cost
