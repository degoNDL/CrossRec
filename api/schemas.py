from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from optimizer.opening_hours import WEEKDAYS_PT

MAX_PONTOS_POR_REQUISICAO = 15  # tamanho do catálogo curado inteiro (Fase 1)

Mode = Literal["walk", "drive"]


def _validar_hora(valor: str) -> str:
    partes = valor.split(":")
    if len(partes) != 2 or not all(p.isdigit() for p in partes):
        raise ValueError(f"Horário inválido: '{valor}'. Use o formato HH:MM.")
    h, m = int(partes[0]), int(partes[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Horário inválido: '{valor}'. Use o formato HH:MM (24h).")
    return f"{h:02d}:{m:02d}"


class RoteiroRequest(BaseModel):
    pontos_ids: list[str] = Field(
        min_length=1,
        max_length=MAX_PONTOS_POR_REQUISICAO,
        description="Ids dos pontos turísticos desejados (ver GET /pontos).",
    )
    dia_semana: str = Field(description=f"Um de: {', '.join(WEEKDAYS_PT)}")
    hora_inicio_dia: str = Field(default="09:00", description="Horário HH:MM em que o dia começa.")
    hora_fim_dia: str = Field(default="18:00", description="Horário HH:MM em que o dia termina.")
    ponto_inicio_id: str | None = Field(
        default=None, description="Id do ponto de partida. Se omitido, o otimizador escolhe o melhor início."
    )
    narrar: bool = Field(
        default=False, description="Se True, a resposta inclui uma narrativa do dia gerada por IA."
    )

    @field_validator("pontos_ids")
    @classmethod
    def sem_duplicatas(cls, valor: list[str]) -> list[str]:
        if len(valor) != len(set(valor)):
            raise ValueError("pontos_ids não pode conter ids repetidos.")
        return valor

    @field_validator("dia_semana")
    @classmethod
    def dia_semana_valido(cls, valor: str) -> str:
        if valor not in WEEKDAYS_PT:
            raise ValueError(f"dia_semana inválido: '{valor}'. Use um de: {', '.join(WEEKDAYS_PT)}.")
        return valor

    @field_validator("hora_inicio_dia", "hora_fim_dia")
    @classmethod
    def hora_valida(cls, valor: str) -> str:
        return _validar_hora(valor)

    @model_validator(mode="after")
    def fim_depois_do_inicio(self) -> "RoteiroRequest":
        inicio = _to_minutes(self.hora_inicio_dia)
        fim = _to_minutes(self.hora_fim_dia)
        if fim <= inicio:
            raise ValueError("hora_fim_dia precisa ser depois de hora_inicio_dia.")
        return self

    @model_validator(mode="after")
    def ponto_inicio_esta_na_lista(self) -> "RoteiroRequest":
        if self.ponto_inicio_id is not None and self.ponto_inicio_id not in self.pontos_ids:
            raise ValueError("ponto_inicio_id precisa estar presente em pontos_ids.")
        return self


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


class ParadaResponse(BaseModel):
    ponto_id: str
    nome: str
    modo_chegada: Mode | None
    hora_chegada: str
    espera_minutos: float
    hora_inicio_visita: str
    hora_fim_visita: str


class RoteiroResponse(BaseModel):
    completo: bool = Field(description="False se nem todos os pontos pedidos couberam no dia (modo Orienteering).")
    paradas: list[ParadaResponse]
    pontos_ignorados_fechados: list[str] = Field(
        description="Ids que estavam fechados no dia da semana escolhido — nem entraram na otimização."
    )
    custo_total_minutos: float = Field(description="Deslocamento + espera somados; não conta tempo de visita.")
    narrativa: str | None = Field(default=None, description="Texto do roteiro narrado por IA, se `narrar=true`.")


class InterpretarRequest(BaseModel):
    texto: str = Field(min_length=3, max_length=500, description="Pedido do turista em linguagem natural.")


class InterpretarResponse(BaseModel):
    pontos_ids: list[str]
    pontos: list[dict] = Field(description="Dados completos dos pontos encontrados, para o turista revisar.")
