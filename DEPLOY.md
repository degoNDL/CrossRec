# Deploy do CrossRec

Backend no Koyeb, frontend na Vercel. Os passos de criar conta e clicar no dashboard só você
pode fazer — aqui vai exatamente o que configurar em cada um.

Sem banco de dados por enquanto: o catálogo de pontos é um JSON estático versionado no
repositório (`data/curated_points.json`), então não há necessidade real de Postgres/Neon
ainda — isso fica para quando o app precisar de dado dinâmico (ex: salvar roteiros de
usuário), na Fase 9.

## 1. Backend no Koyeb

1. Crie uma conta em [koyeb.com](https://www.koyeb.com) (dá para entrar direto com o GitHub).
2. No dashboard, **Create Service** → **GitHub** → autorize o Koyeb a acessar o repositório
   `degoNDL/CrossRec` e selecione-o.
3. Configuração do build:
   - **Builder**: Dockerfile
   - **Dockerfile location**: `docker/Dockerfile.api`
   - **Build context**: raiz do repositório (`.`)
   - **Branch**: `main`
   - **Port**: `8000`
4. Variáveis de ambiente (**Environment Variables**):
   - `GROQ_API_KEY` → cole sua chave do Groq (a mesma do seu `.env` local)
   - `CORS_ORIGINS` → deixe em branco por enquanto; você volta aqui depois que a Vercel gerar
     a URL do frontend (passo 3 abaixo)
5. Clique em **Deploy**. O primeiro build demora alguns minutos (instala OSMnx e afins) —
   normal.
6. Quando terminar, o Koyeb dá uma URL pública tipo `https://crossrec-api-xxxx.koyeb.app`.
   Teste abrindo `<essa-url>/pontos` (deve devolver o catálogo em JSON) ou `<essa-url>/docs`
   (Swagger interativo).
7. **Guarde essa URL** — é o `NEXT_PUBLIC_API_URL` do próximo passo.

## 2. Frontend na Vercel

1. Crie uma conta em [vercel.com](https://vercel.com) (login com GitHub).
2. **Add New** → **Project** → importe o repositório `degoNDL/CrossRec`.
3. Configuração:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js (a Vercel detecta sozinha)
4. Variável de ambiente:
   - `NEXT_PUBLIC_API_URL` → a URL do Koyeb que você guardou no passo anterior (sem barra no
     final, ex: `https://crossrec-api-xxxx.koyeb.app`)
5. **Deploy**. Ao terminar, a Vercel dá uma URL tipo `https://crossrec.vercel.app` — esse é o
   link público do app.

## 3. Fechar o CORS

Volte no Koyeb, na variável `CORS_ORIGINS` do serviço da API, e coloque a URL da Vercel do
passo anterior (ex: `https://crossrec.vercel.app`). Salve — o Koyeb reinicia o serviço
sozinho. Sem isso, o navegador bloqueia as chamadas do frontend pra API por CORS.

## 4. Testar de ponta a ponta

Abra a URL da Vercel, selecione alguns pontos, calcule um roteiro. Se der erro de rede,
confira:
- a URL em `NEXT_PUBLIC_API_URL` na Vercel está exatamente igual à URL pública do Koyeb (sem
  barra no final)?
- `CORS_ORIGINS` no Koyeb tem a URL certa da Vercel?
- o serviço no Koyeb está com status "Healthy" no dashboard?

## Redeploy automático

Tanto Koyeb quanto Vercel ficam observando o branch `main` — todo `git push` nele dispara um
novo deploy automaticamente em ambos.
