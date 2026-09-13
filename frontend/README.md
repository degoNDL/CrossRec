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
- `src/components/MapaRota.tsx` — mapa (Leaflet + tiles CARTO Dark Matter, sem chave de API) com
  marcadores numerados na ordem de visita (entrada animada em sequência) e trechos coloridos por
  modo (teal = a pé, coral = carro), com o traçado se desenhando via animação de `stroke-dashoffset`.
- `src/components/LinhaDoTempo.tsx` — linha do tempo do dia com horários e modo de chegada.
- `src/lib/api.ts` — cliente HTTP para a API (`GET /pontos`, `POST /roteiro`, `POST /interpretar`).

## Identidade visual

Tema escuro único (não é "dark mode" alternativo a um claro — ver decisão abaixo), inspirado no
Recife à noite: fundo azul-petróleo profundo, acento coral (pôr do sol de Boa Viagem) e teal
(mar). Tipografia: Fraunces (serifada editorial, títulos) + Plus Jakarta Sans (interface).
Animações via `framer-motion` (entradas em cascata) e CSS puro (blobs decorativos, marcadores do
mapa). Tokens de cor em `src/app/globals.css` (`--bg`, `--coral`, `--teal` etc.).

## Decisões e limitações assumidas

- Mapa usa tiles públicos (CARTO Dark Matter, que reusa dados OpenStreetMap) em vez de Google
  Maps/Mapbox — mantém o princípio de infraestrutura de custo zero do projeto, sem chave de API.
- As linhas do mapa entre paradas são retas (não seguem a rua real). A API hoje só retorna a
  decisão de ordem/modo/horário, não a geometria do caminho — desenhar o trajeto real exigiria a
  API devolver a polyline do OSMnx, o que não estava no escopo desta fase.
- `reactStrictMode` está desligado (`next.config.ts`): Leaflet inicializa o mapa imperativamente
  num nó do DOM, e o duplo-efeito do Strict Mode em dev (monta/desmonta/monta) faz o Leaflet
  achar que o container já está em uso por outra instância. É uma incompatibilidade conhecida
  react-leaflet + Strict Mode, não afeta o build de produção (`next build`, já testado).
