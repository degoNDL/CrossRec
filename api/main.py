"""API do CrossRec: recebe os pontos que o turista quer visitar e devolve o
roteiro otimizado (ordem, modo de cada trecho, horários).

Uso local:
    uvicorn api.main:app --reload
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai.nl_to_points import traduzir_desejo
from ai.narrate import narrar_roteiro
from api.schemas import (
    InterpretarRequest,
    InterpretarResponse,
    ParadaResponse,
    RoteiroRequest,
    RoteiroResponse,
)
from data.schema import TouristPoint
from optimizer.cost import CostModel
from optimizer.itinerary import solve

logger = logging.getLogger("crossrec.api")

CURATED_POINTS_PATH = Path(__file__).parent.parent / "data" / "curated_points.json"

_estado: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carregado uma vez na subida da API — as matrizes já estão cacheadas em
    # disco (Fase 2), então isso é rápido (leitura de JSON, não recálculo).
    _estado["catalogo"] = json.loads(CURATED_POINTS_PATH.read_text(encoding="utf-8"))
    _estado["catalogo_por_id"] = {p["id"]: p for p in _estado["catalogo"]}
    _estado["cost_model"] = CostModel.load()
    logger.info("CrossRec API pronta: %d pontos no catálogo.", len(_estado["catalogo"]))
    yield
    _estado.clear()


app = FastAPI(
    title="CrossRec API",
    description="Otimizador multimodal de rotas turísticas para o Recife.",
    version="0.1.0",
    lifespan=lifespan,
)

# Origens do frontend que podem chamar a API. Em dev é sempre localhost;
# em produção (Fase 7) a URL da Vercel entra via variável de ambiente —
# nunca hardcoded, para não precisar alterar código a cada novo deploy.
_origens_extra = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", *_origens_extra],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Mensagens de erro do Pydantic já são específicas (ver api/schemas.py);
    # só achatamos para um formato simples de ler em vez do padrão aninhado.
    erros = [
        {"campo": ".".join(str(p) for p in err["loc"] if p != "body"), "mensagem": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": "Entrada inválida.", "erros": erros})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno ao calcular o roteiro. Tente novamente em instantes."},
    )


@app.get("/pontos", response_model=list[TouristPoint])
def listar_pontos():
    """Catálogo de pontos turísticos curados disponíveis para montar um roteiro."""
    return _estado["catalogo"]


@app.post("/interpretar", response_model=InterpretarResponse)
def interpretar_pedido(pedido: InterpretarRequest):
    """Traduz um pedido em linguagem natural para ids do catálogo, via IA.
    Não calcula o roteiro — devolve os pontos encontrados para o turista
    revisar/ajustar antes de chamar POST /roteiro."""

    catalogo = _estado["catalogo"]
    try:
        ids = traduzir_desejo(pedido.texto, catalogo)
    except Exception:
        logger.exception("Falha ao interpretar pedido em linguagem natural")
        raise HTTPException(
            status_code=502,
            detail="Não foi possível interpretar o pedido agora (serviço de IA indisponível). "
            "Tente de novo em instantes ou monte o roteiro escolhendo os pontos em GET /pontos.",
        )

    catalogo_por_id = _estado["catalogo_por_id"]
    return InterpretarResponse(pontos_ids=ids, pontos=[catalogo_por_id[pid] for pid in ids])


@app.post("/roteiro", response_model=RoteiroResponse)
def calcular_roteiro(pedido: RoteiroRequest):
    catalogo_por_id = _estado["catalogo_por_id"]

    nao_encontrados = [pid for pid in pedido.pontos_ids if pid not in catalogo_por_id]
    if nao_encontrados:
        raise HTTPException(
            status_code=404,
            detail=f"Ponto(s) não encontrado(s) no catálogo: {', '.join(nao_encontrados)}. "
            "Consulte GET /pontos para ver os ids válidos.",
        )

    pontos = [catalogo_por_id[pid] for pid in pedido.pontos_ids]
    cost_model: CostModel = _estado["cost_model"]

    itinerario = solve(
        pontos,
        cost_model,
        weekday=pedido.dia_semana,
        hora_inicio_dia=pedido.hora_inicio_dia,
        hora_fim_dia=pedido.hora_fim_dia,
        start_id=pedido.ponto_inicio_id,
    )

    paradas = [
        ParadaResponse(
            ponto_id=p.ponto_id,
            nome=catalogo_por_id[p.ponto_id]["nome"],
            modo_chegada=p.modo_chegada,
            hora_chegada=p.hora_chegada,
            espera_minutos=p.espera_minutos,
            hora_inicio_visita=p.hora_inicio_visita,
            hora_fim_visita=p.hora_fim_visita,
        )
        for p in itinerario.paradas
    ]

    narrativa = None
    if pedido.narrar:
        try:
            narrativa = narrar_roteiro([p.model_dump() for p in paradas])
        except Exception:
            logger.exception("Falha ao narrar roteiro")
            narrativa = None  # roteiro em si já é válido — não falha a requisição por causa da narração

    return RoteiroResponse(
        completo=itinerario.completo,
        paradas=paradas,
        pontos_ignorados_fechados=itinerario.pontos_ignorados_fechados,
        custo_total_minutos=itinerario.custo_total_minutos,
        narrativa=narrativa,
    )
