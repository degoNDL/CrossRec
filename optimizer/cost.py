"""Função de custo multimodal: dado um par de pontos, decide se o melhor é
ir a pé ou de carro, e quanto tempo isso leva.

A decisão é local a cada trecho (não por viagem inteira), o que é o que
permite ao otimizador (Fase 3) escolher o modo trecho a trecho junto com a
ordem de visita. Dirigir carrega uma penalidade fixa de troca de modo
(pegar o carro, estacionar ou chamar o transporte) — sem ela, o carro
pareceria sempre melhor, mesmo para o quarteirão ao lado.
"""

from dataclasses import dataclass
from typing import Literal

from optimizer.matrices import build_all_matrices

Mode = Literal["walk", "drive"]

# Penalidade fixa de troca de modo, em minutos, cobrada apenas quando o
# trecho é feito de carro. Representa o tempo de pegar o carro/estacionar
# ou chamar um transporte por aplicativo — não o tempo de trânsito em si.
MODE_SWITCH_PENALTY_MINUTES = 6.0


@dataclass(frozen=True)
class TrechoCusto:
    mode: Mode
    minutes: float


class CostModel:
    """Encapsula as matrizes de tempo (a pé e de carro) já carregadas, para
    não recarregar do disco a cada consulta de par de pontos."""

    def __init__(self, walk_matrix: dict, drive_matrix: dict):
        self._walk_matrix = walk_matrix
        self._drive_matrix = drive_matrix

    @classmethod
    def load(cls) -> "CostModel":
        walk_matrix, drive_matrix = build_all_matrices()
        return cls(walk_matrix, drive_matrix)

    def cost(self, origin_id: str, dest_id: str) -> TrechoCusto:
        if origin_id == dest_id:
            return TrechoCusto(mode="walk", minutes=0.0)

        walk_minutes = self._walk_matrix.get(origin_id, {}).get(dest_id)
        drive_minutes_raw = self._drive_matrix.get(origin_id, {}).get(dest_id)
        drive_minutes = (
            drive_minutes_raw + MODE_SWITCH_PENALTY_MINUTES
            if drive_minutes_raw is not None
            else None
        )

        if walk_minutes is None and drive_minutes is None:
            raise ValueError(
                f"Nenhum caminho encontrado entre '{origin_id}' e '{dest_id}' "
                "nem a pé nem de carro — verifique se os pontos estão conectados ao grafo."
            )
        if walk_minutes is None:
            return TrechoCusto(mode="drive", minutes=drive_minutes)
        if drive_minutes is None:
            return TrechoCusto(mode="walk", minutes=walk_minutes)

        if walk_minutes <= drive_minutes:
            return TrechoCusto(mode="walk", minutes=walk_minutes)
        return TrechoCusto(mode="drive", minutes=drive_minutes)

    def raw_time(self, origin_id: str, dest_id: str, mode: Mode) -> float | None:
        """Tempo de deslocamento em minutos para um modo específico, SEM a
        penalidade de troca — quem decide se/quando cobrar a penalidade é
        quem chama isto (o otimizador, que sabe se o turista já estava
        naquele modo no trecho anterior). `None` se não há caminho nesse
        modo entre os dois pontos."""

        if origin_id == dest_id:
            return 0.0
        matrix = self._walk_matrix if mode == "walk" else self._drive_matrix
        return matrix.get(origin_id, {}).get(dest_id)
