from typing import Optional

from pydantic import BaseModel, Field


class TouristPoint(BaseModel):
    """Um ponto turístico curado do Recife, pronto para o otimizador."""

    id: str = Field(description="Identificador único e estável (slug), ex: 'marco-zero'")
    nome: str
    endereco: str
    latitude: float
    longitude: float
    categoria: str = Field(description="museu, historico, praia, mercado, parque, religioso ou cultural")
    horario_funcionamento: dict[str, str] = Field(
        description="Mapa de dia/período -> horário, ex: {'terca_sexta': '09:00-17:00'}"
    )
    fecha_segunda: bool
    tempo_visita_sugerido_minutos: int
    fonte: Optional[str] = Field(default=None, description="URL usada para validar o horário")
    observacoes: Optional[str] = None
