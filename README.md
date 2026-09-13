# CrossRec

Otimizador multimodal de rotas turísticas para o Recife.

🔗 **[cross-rec.vercel.app](https://cross-rec.vercel.app)** — app no ar (backend em
[crossrec.onrender.com](https://crossrec.onrender.com), free tier: a primeira requisição
depois de um tempo sem uso pode demorar ~30-50s para "acordar" o serviço).

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
| Infra | Docker, GitHub Actions, Render |

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
- [x] Fase 4 — API
- [x] Fase 5 — Camada de IA
- [x] Fase 6 — Frontend
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

## Rodando a API

```bash
uvicorn api.main:app --reload
```

- `GET /pontos` — catálogo de pontos turísticos disponíveis.
- `POST /roteiro` — calcula o roteiro otimizado. Corpo de exemplo:

```json
{
  "pontos_ids": ["marco-zero", "paco-do-frevo", "mercado-sao-jose"],
  "dia_semana": "quinta",
  "hora_inicio_dia": "09:00",
  "hora_fim_dia": "18:00",
  "narrar": true
}
```

- `POST /interpretar` — traduz um pedido em linguagem natural para ids do catálogo,
  via IA (Groq). Não calcula o roteiro, só sugere os pontos:

```json
{"texto": "quero ver o centro histórico e terminar numa praia"}
```

Requer `GROQ_API_KEY` em `.env` (copie de `.env.example`) para `/interpretar` e para
`/roteiro` com `"narrar": true`.

Docs interativas (Swagger) em `http://127.0.0.1:8000/docs` com o servidor rodando.

## Rodando o frontend

```bash
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:3000` (precisa da API rodando em paralelo). Ver [frontend/README.md](frontend/README.md).

## Rodando com Docker

```bash
docker compose up --build
```

Sobe a API em `http://localhost:8000` e o frontend em `http://localhost:3000` juntos. As
matrizes de custo (`data/cache/matrix_*.json`) já vêm versionadas no repositório, então o
build não depende de baixar o grafo de ruas do Recife — só é necessário reconstruí-lo se o
conjunto de pontos curados mudar (ver [data/README.md](data/README.md)).

## Deploy

Backend no [Render](https://render.com) (a partir de `docker/Dockerfile.api`) e frontend na
[Vercel](https://vercel.com) (build nativo do Next.js, a partir de `frontend/`). Passo a passo
em [DEPLOY.md](DEPLOY.md).

## Licença

MIT — ver [LICENSE](LICENSE).
