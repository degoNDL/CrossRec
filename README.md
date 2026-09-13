# CrossRec

Otimizador multimodal de rotas turísticas para o Recife.

🔗 **[cross-rec.vercel.app](https://cross-rec.vercel.app)** está no ar.

## O problema

O trânsito e o deslocamento no Recife podem ser bastante caóticos, e uma boa gestão de
tempo e locomoção nesse contexto ajuda muito quem está de passagem pela cidade. O turista
sabe quais pontos quer visitar, mas não sabe em que ordem percorrê-los nem quando vale ir
a pé ou de carro. O CrossRec recebe os pontos desejados e devolve a melhor ordem, o modo
de transporte de cada trecho e os horários estimados do dia, respeitando o funcionamento
de cada atração.

Por baixo é uma variação do problema do caixeiro viajante (TSP): um TSP multimodal com
janela de tempo, resolvido de forma exata por programação dinâmica (Held-Karp) na escala
de um turista, com fallback para meta-heurística e para um modo Orienteering quando nem
tudo cabe no dia.

O propósito deste projeto pessoal é aprimorar conhecimentos próprios acerca de otimização
combinatória, integração de modelos de linguagem em produtos reais e desenvolvimento
full-stack (backend em Python/FastAPI, frontend em Next.js, geoprocessamento com OSMnx).

Melhorias que estão no escopo futuro do projeto:

- Adição de mais pontos turísticos ao catálogo curado
- Preços de entrada de cada atração
- Sugestão do melhor local para estacionar em cada parada feita de carro
- Integração com previsão do tempo, para sugerir roteiros alternativos em dias de chuva

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

## Licença

MIT — ver [LICENSE](LICENSE).
