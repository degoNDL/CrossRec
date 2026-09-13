# optimizer/

O núcleo do CrossRec (Fase 3): dada uma lista de pontos, decide a melhor ordem, o modo
de transporte de cada trecho e os horários do dia — de forma exata para o tamanho real
de uso (um turista, poucos pontos), com fallback de meta-heurística para escala maior.

## Módulos

- `held_karp.py` — Held-Karp clássico (TSP de caminho, bitmask DP), a referência de
  corretude. Testado contra força bruta em `tests/test_held_karp.py`.
- `simple_tsp.py` — passo 1: só a ordem, usando o custo multimodal combinado por
  trecho (`CostModel.cost`), sem encadear o modo entre trechos consecutivos.
- `opening_hours.py` — converte o horário semi-livre de `curated_points.json` num
  horário semanal estruturado, consultável por dia da semana.
- `itinerary.py` — o otimizador completo (passos 2-4): o estado da DP carrega também o
  modo de transporte do trecho anterior (a penalidade de troca só é cobrada quando o
  modo realmente muda, não a cada trecho de carro), respeita a janela de funcionamento
  e o tempo de visita de cada ponto, e cai automaticamente no modo Orienteering
  (melhor subconjunto possível) quando nem tudo cabe no dia.
- `genetic.py` — algoritmo genético memético (crossover de ordem + mutação por
  inversão + busca local 2-opt no elite) para quando o problema cresce além do que o
  Held-Karp exato resolve em tempo viável (a partir de ~15-18 pontos).
- `benchmark.py` — compara Held-Karp exato vs GA em instâncias pequenas (deve quase
  empatar) e GA vs OR-Tools em instâncias grandes (`python -m optimizer.benchmark`).

## Decisões e limitações assumidas

- O passeio é um **caminho**, não um ciclo — não volta ao ponto de partida.
- Cada ponto tem só **uma** janela diária (ver limitação em `opening_hours.py` sobre
  horários partidos, ex: fecha para almoço).
- O GA/benchmark usa instâncias com estrutura geográfica (distância euclidiana / matriz
  real do Recife), não custos aleatórios sem desigualdade triangular — é o cenário que
  o problema real tem, e onde 2-opt/GA/OR-Tools de fato são desenhados para funcionar
  bem. Testado com `tests/test_genetic.py`.
