"""O otimizador completo: dada uma lista de pontos, devolve a melhor ordem,
o modo de cada trecho e os horários do dia, respeitando o funcionamento de
cada ponto — ou, quando nem tudo cabe no dia, o melhor subconjunto possível
(modo Orienteering).

Diferença para `simple_tsp.py` (passo 1): aqui o estado da programação
dinâmica carrega também o modo de transporte do trecho anterior, então a
penalidade de troca de modo só é cobrada quando o modo realmente muda entre
dois trechos consecutivos — dirigir vários trechos seguidos paga a
penalidade uma vez, não a cada trecho. Isso dobra o espaço de estados
(mask, último ponto) -> (mask, último ponto, último modo), como descrito no
roadmap, e ainda é trivial na escala de um turista (n <= ~15).

O problema deixa de ser um TSP de custo aditivo simples e passa a ser um
problema de caminho mínimo sobre um grafo de estados (mask, nó, modo), onde
"custo" é o horário de término da visita — daí a DP ser feita por expansão
em camadas (BFS por número de pontos visitados) em vez da forma fechada de
`held_karp.py`.

Suposições assumidas de propósito, documentadas para não virar surpresa:
- O passeio é um CAMINHO, não um ciclo: o turista não precisa voltar ao
  ponto de partida no fim do dia.
- Cada ponto só tem UMA janela diária (ver limitação em `opening_hours.py`
  sobre horários partidos).
"""

from dataclasses import dataclass

from optimizer.cost import MODE_SWITCH_PENALTY_MINUTES, CostModel, Mode
from optimizer.opening_hours import to_hhmm, to_minutes, window_for_weekday


@dataclass
class Parada:
    ponto_id: str
    modo_chegada: Mode | None  # None para o primeiro ponto do dia
    hora_chegada: str
    espera_minutos: float
    hora_inicio_visita: str
    hora_fim_visita: str


@dataclass
class Itinerario:
    paradas: list[Parada]
    completo: bool  # True: todos os pontos candidatos couberam no dia
    pontos_ignorados_fechados: list[str]  # fechados no dia da semana escolhido
    custo_total_minutos: float  # deslocamento + espera (não conta tempo de visita)


def _candidatos(points: list[dict], weekday: str) -> tuple[list[dict], list[str]]:
    candidatos = []
    ignorados = []
    for p in points:
        window = window_for_weekday(p["horario_funcionamento"], weekday)
        if window is None:
            ignorados.append(p["id"])
        else:
            candidatos.append(p)
    return candidatos, ignorados


def _tentar_visitar(chegada: float, janela: tuple[int, int], duracao: int) -> tuple[float, float] | None:
    abertura, fechamento = janela
    inicio_visita = max(chegada, abertura)
    fim_visita = inicio_visita + duracao
    if fim_visita > fechamento:
        return None
    return fim_visita, inicio_visita


def _resolver_estados(
    candidatos: list[dict],
    cost_model: CostModel,
    weekday: str,
    hora_inicio_dia: float,
    hora_fim_dia: float,
    start_id: str | None,
) -> tuple[dict, dict, dict]:
    """Roda a DP por camadas e devolve (all_states, parent, seed_info)."""

    n = len(candidatos)
    ids = [p["id"] for p in candidatos]
    duracoes = [p["tempo_visita_sugerido_minutos"] for p in candidatos]
    janelas = [window_for_weekday(p["horario_funcionamento"], weekday) for p in candidatos]

    start_indices = (
        [ids.index(start_id)] if start_id is not None else list(range(n))
    )

    all_states: dict = {}
    seed_info: dict = {}
    parent: dict = {}

    current_layer: dict = {}
    for s in start_indices:
        resultado = _tentar_visitar(hora_inicio_dia, janelas[s], duracoes[s])
        if resultado is None:
            continue
        fim, inicio_visita = resultado
        key = (1 << s, s, None)
        current_layer[key] = fim
        seed_info[key] = (hora_inicio_dia, inicio_visita, fim)

    all_states.update(current_layer)

    for _ in range(n - 1):
        next_layer: dict = {}
        for (mask, k, modo_k), fim_k in current_layer.items():
            for j in range(n):
                if mask & (1 << j):
                    continue
                for novo_modo in ("walk", "drive"):
                    deslocamento = cost_model.raw_time(ids[k], ids[j], novo_modo)
                    if deslocamento is None:
                        continue
                    # A penalidade representa pegar o carro/estacionar — só
                    # entra quando o trecho é de carro E o trecho anterior
                    # não era (senão o turista já está com o carro em mãos).
                    # Caminhar nunca é penalizado (mesma regra de cost.py).
                    penalidade = (
                        MODE_SWITCH_PENALTY_MINUTES
                        if (novo_modo == "drive" and modo_k != "drive")
                        else 0.0
                    )
                    chegada = fim_k + deslocamento + penalidade
                    resultado = _tentar_visitar(chegada, janelas[j], duracoes[j])
                    if resultado is None:
                        continue
                    fim_j, inicio_visita_j = resultado
                    if fim_j > hora_fim_dia:
                        continue

                    novo_mask = mask | (1 << j)
                    key = (novo_mask, j, novo_modo)
                    if key not in next_layer or fim_j < next_layer[key]:
                        next_layer[key] = fim_j
                        parent[key] = (mask, k, modo_k, chegada, inicio_visita_j)

        all_states.update(next_layer)
        current_layer = next_layer
        if not current_layer:
            break

    return all_states, parent, seed_info


def _reconstruir(
    key: tuple[int, int, str | None],
    parent: dict,
    seed_info: dict,
    ids: list[str],
) -> list[dict]:
    paradas_reversas = []
    while key not in seed_info:
        mask, j, modo_j = key
        prev_mask, k, modo_k, chegada, inicio_visita = parent[key]
        paradas_reversas.append((j, modo_j, chegada, inicio_visita))
        key = (prev_mask, k, modo_k)

    hora_inicio_dia, inicio_visita_0, fim_0 = seed_info[key]
    _, primeiro_idx, _ = key
    paradas_reversas.append((primeiro_idx, None, hora_inicio_dia, inicio_visita_0))

    paradas_reversas.reverse()

    # recalcula hora_fim_visita de cada parada (= próxima "chegada" menos
    # deslocamento não é direto de recuperar aqui; em vez disso, cada parada
    # sabe sua própria duração via inicio_visita + duração do ponto).
    paradas: list[Parada] = []
    for idx, (ponto_idx, modo, chegada, inicio_visita) in enumerate(paradas_reversas):
        paradas.append(
            {
                "ponto_idx": ponto_idx,
                "modo": modo,
                "chegada": chegada,
                "inicio_visita": inicio_visita,
            }
        )
    return paradas


def _montar_itinerario(
    candidatos: list[dict],
    ids: list[str],
    key_final: tuple[int, int, str | None],
    all_states: dict,
    parent: dict,
    seed_info: dict,
    ignorados: list[str],
    completo: bool,
) -> Itinerario:
    brutos = _reconstruir(key_final, parent, seed_info, ids)

    paradas = []
    custo_total = 0.0
    hora_dia_anterior_fim = None
    for item in brutos:
        idx = item["ponto_idx"]
        duracao = candidatos[idx]["tempo_visita_sugerido_minutos"]
        inicio_visita = item["inicio_visita"]
        fim_visita = inicio_visita + duracao
        chegada = item["chegada"]
        espera = inicio_visita - chegada

        paradas.append(
            Parada(
                ponto_id=candidatos[idx]["id"],
                modo_chegada=item["modo"],
                hora_chegada=to_hhmm(chegada),
                espera_minutos=round(espera, 1),
                hora_inicio_visita=to_hhmm(inicio_visita),
                hora_fim_visita=to_hhmm(fim_visita),
            )
        )
        if hora_dia_anterior_fim is not None:
            custo_total += (chegada - hora_dia_anterior_fim) + espera
        hora_dia_anterior_fim = fim_visita

    return Itinerario(
        paradas=paradas,
        completo=completo,
        pontos_ignorados_fechados=ignorados,
        custo_total_minutos=round(custo_total, 1),
    )


def solve(
    points: list[dict],
    cost_model: CostModel,
    weekday: str,
    hora_inicio_dia: str = "09:00",
    hora_fim_dia: str = "18:00",
    start_id: str | None = None,
) -> Itinerario:
    """Tenta encaixar TODOS os pontos candidatos no dia; se não couber,
    cai automaticamente no modo Orienteering (melhor subconjunto possível).
    """

    candidatos, ignorados = _candidatos(points, weekday)
    if not candidatos:
        return Itinerario(paradas=[], completo=True, pontos_ignorados_fechados=ignorados, custo_total_minutos=0.0)

    ids = [p["id"] for p in candidatos]
    n = len(candidatos)
    full_mask = (1 << n) - 1

    all_states, parent, seed_info = _resolver_estados(
        candidatos,
        cost_model,
        weekday,
        to_minutes(hora_inicio_dia),
        to_minutes(hora_fim_dia),
        start_id,
    )

    # Tenta o conjunto completo primeiro.
    completos = [k for k in all_states if k[0] == full_mask]
    if completos:
        melhor = min(completos, key=lambda k: all_states[k])
        return _montar_itinerario(candidatos, ids, melhor, all_states, parent, seed_info, ignorados, completo=True)

    # Orienteering: maximiza quantos pontos entram, desempate por término mais cedo.
    if not all_states:
        return Itinerario(paradas=[], completo=False, pontos_ignorados_fechados=ignorados, custo_total_minutos=0.0)

    melhor = max(all_states, key=lambda k: (bin(k[0]).count("1"), -all_states[k]))
    return _montar_itinerario(candidatos, ids, melhor, all_states, parent, seed_info, ignorados, completo=False)
