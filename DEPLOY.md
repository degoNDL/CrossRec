# Deploy do CrossRec

Backend no Render, frontend na Vercel. Os passos de criar conta e clicar no dashboard só você
pode fazer — aqui vai exatamente o que configurar em cada um.

> O roadmap original previa o backend no Koyeb, mas o Koyeb saiu do ar (adquirido pela
> Mistral AI). O Render é o substituto direto: free tier sem cartão de crédito, deploy via
> Dockerfile a partir do GitHub — a configuração é equivalente.

Sem banco de dados por enquanto: o catálogo de pontos é um JSON estático versionado no
repositório (`data/curated_points.json`), então não há necessidade real de Postgres/Neon
ainda — isso fica para quando o app precisar de dado dinâmico (ex: salvar roteiros de
usuário), na Fase 9.

## 1. Backend no Render

1. Crie uma conta em [render.com](https://render.com) (dá para entrar direto com o GitHub).
2. No dashboard, **New** → **Web Service** → conecte sua conta do GitHub e selecione o
   repositório `degoNDL/CrossRec`.
3. Configuração do build:
   - **Language/Runtime**: Docker
   - **Dockerfile Path**: `docker/Dockerfile.api`
   - **Docker Build Context Directory**: raiz do repositório (`.`)
   - **Branch**: `main`
   - **Instance Type**: Free
4. Variáveis de ambiente (**Environment**):
   - `GROQ_API_KEY` → cole sua chave do Groq (a mesma do seu `.env` local)
   - `CORS_ORIGINS` → deixe em branco por enquanto; você volta aqui depois que a Vercel gerar
     a URL do frontend (passo 3 abaixo)
   - O Render injeta `PORT` sozinho — não precisa configurar, o `docker/Dockerfile.api` já
     escuta na porta que ele passar.
5. Clique em **Create Web Service**. O primeiro build demora alguns minutos (instala OSMnx e
   afins) — normal.
6. Quando terminar, o Render dá uma URL pública tipo `https://crossrec-api.onrender.com`.
   Teste abrindo `<essa-url>/pontos` (deve devolver o catálogo em JSON) ou `<essa-url>/docs`
   (Swagger interativo).
7. **Guarde essa URL** — é o `NEXT_PUBLIC_API_URL` do próximo passo.

**Atenção ao free tier do Render**: o serviço "dorme" depois de ~15 minutos sem receber
requisição, e a próxima requisição acorda ele de novo — isso leva uns 30-50 segundos. É
esperado e normal num free tier; vale mencionar isso no README (Fase 8) para quem for testar
o link publicado não estranhar a primeira resposta demorada.

## 2. Frontend na Vercel

1. Crie uma conta em [vercel.com](https://vercel.com) (login com GitHub).
2. **Add New** → **Project** → importe o repositório `degoNDL/CrossRec`.
3. Configuração:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js (a Vercel detecta sozinha)
4. Variável de ambiente:
   - `NEXT_PUBLIC_API_URL` → a URL do Render que você guardou no passo anterior (sem barra no
     final, ex: `https://crossrec-api.onrender.com`)
5. **Deploy**. Ao terminar, a Vercel dá uma URL tipo `https://crossrec.vercel.app` — esse é o
   link público do app.

## 3. Fechar o CORS

Volte no Render, na variável `CORS_ORIGINS` do serviço da API, e coloque a URL da Vercel do
passo anterior (ex: `https://crossrec.vercel.app`). Salve — o Render reinicia o serviço
sozinho. Sem isso, o navegador bloqueia as chamadas do frontend pra API por CORS.

## 4. Testar de ponta a ponta

Abra a URL da Vercel, selecione alguns pontos, calcule um roteiro. Lembre que a primeira
chamada pode demorar (Render acordando, ver aviso acima). Se der erro persistente, confira:
- a URL em `NEXT_PUBLIC_API_URL` na Vercel está exatamente igual à URL pública do Render (sem
  barra no final)?
- `CORS_ORIGINS` no Render tem a URL certa da Vercel?
- o serviço no Render está com status "Live" no dashboard?

## Redeploy automático

Tanto Render quanto Vercel ficam observando o branch `main` — todo `git push` nele dispara um
novo deploy automaticamente em ambos.
