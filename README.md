# CrossRec

Otimizador multimodal de rotas turísticas para o Recife.

## O problema

O turista sabe quais pontos do Recife quer visitar, mas não sabe em que ordem
percorrê-los nem quando vale ir a pé ou de carro. O CrossRec recebe os pontos
desejados e devolve a melhor ordem, o modo de transporte de cada trecho e os
horários estimados do dia, respeitando o funcionamento de cada atração.

Por baixo é uma variação do problema do caixeiro viajante (TSP): um TSP
multimodal com janela de tempo, resolvido de forma exata por programação
dinâmica (Held-Karp) na escala de um turista, com fallback para
meta-heurística e para um modo Orienteering quando nem tudo cabe no dia.

## Stack

| Camada | Ferramenta |
|---|---|
| Otimização | Python, Held-Karp próprio, meta-heurística própria, OR-Tools (benchmark) |
| Dados de pontos | Overpass API (OpenStreetMap) |
| Grafo de ruas | OSMnx |
| Dados de tráfego | Portal de dados abertos do Recife |
| Backend | FastAPI |
| IA | Groq (LLaMA) / Google Gemini |
| Frontend | Next.js |
| Persistência | JSON local → PostgreSQL (Neon) |
| Cache/fila | Upstash Redis |
| Infra | Docker, GitHub Actions, Koyeb |

## Estrutura do repositório

```
crossrec/
  data/          # coleta e curadoria dos pontos e do grafo
  optimizer/     # Held-Karp, meta-heurística, funções de custo
  api/           # FastAPI
  ai/            # integração com o LLM
  frontend/      # Next.js
  tests/         # testes automatizados
  docker/        # Dockerfiles e compose
```

## Status

Projeto em desenvolvimento por fases. Ver roadmap abaixo.

- [x] Fase 0 — Fundação
- [x] Fase 1 — Dados dos pontos turísticos
- [x] Fase 2 — Grafo e matrizes de custo multimodal
- [x] Fase 3 — Otimizador (Held-Karp + janelas de tempo + Orienteering + meta-heurística)
- [ ] Fase 4 — API
- [ ] Fase 5 — Camada de IA
- [ ] Fase 6 — Frontend
- [ ] Fase 7 — Infra e deploy
- [ ] Fase 8 — Qualidade e vitrine
- [ ] Fase 9 — Evolução

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
```

## Rodando com Docker

```bash
docker build -f docker/Dockerfile -t crossrec .
docker run --rm crossrec
```

## Licença

MIT — ver [LICENSE](LICENSE).
