# frontend/

Interface web do CrossRec (Fase 6): Next.js (App Router, TypeScript, Tailwind).

## Rodando localmente

```bash
npm install
npm run dev
```

Precisa da API rodando em `http://localhost:8000` (ver `../README.md`). A URL da API vem de
`NEXT_PUBLIC_API_URL` (`.env.local`, já configurado para dev).

## Estrutura

- `src/app/page.tsx` — a página principal: seleção de pontos, configurações do dia, resultado.
- `src/components/SeletorPontos.tsx` — busca/adiciona pontos do catálogo.
- `src/components/MapaRota.tsx` — mapa (Leaflet + OpenStreetMap, sem chave de API) com marcadores
  numerados na ordem de visita e linhas coloridas por modo (azul = a pé, laranja = carro).
- `src/components/LinhaDoTempo.tsx` — linha do tempo do dia com horários e modo de chegada.
- `src/lib/api.ts` — cliente HTTP para a API (`GET /pontos`, `POST /roteiro`, `POST /interpretar`).

## Decisões e limitações assumidas

- Mapa usa OpenStreetMap (tiles públicos, sem chave de API) em vez de Google Maps/Mapbox — mantém
  o princípio de infraestrutura de custo zero do projeto.
- As linhas do mapa entre paradas são retas (não seguem a rua real). A API hoje só retorna a
  decisão de ordem/modo/horário, não a geometria do caminho — desenhar o trajeto real exigiria a
  API devolver a polyline do OSMnx, o que não estava no escopo desta fase.
- `reactStrictMode` está desligado (`next.config.ts`): Leaflet inicializa o mapa imperativamente
  num nó do DOM, e o duplo-efeito do Strict Mode em dev (monta/desmonta/monta) faz o Leaflet
  achar que o container já está em uso por outra instância. É uma incompatibilidade conhecida
  react-leaflet + Strict Mode, não afeta o build de produção (`next build`, já testado).
