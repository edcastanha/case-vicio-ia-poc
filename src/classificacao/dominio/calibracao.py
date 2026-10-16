import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Rotulo:
    pontuacao: float
    acertou: bool


@dataclass(frozen=True)
class Calibracao:
    limiar: float | None
    precisao_prevista: float
    intervalo: tuple[float, float] = (0.0, 0.0)


def calibrar(amostra: Sequence[Rotulo], alvo: float) -> Calibracao:
    if not amostra:
        raise ValueError("calibração exige ao menos um rótulo")
    melhor = Calibracao(limiar=None, precisao_prevista=0.0)
    for limiar in sorted({r.pontuacao for r in amostra}, reverse=True):
        acima = [r for r in amostra if r.pontuacao >= limiar]
        precisao = sum(r.acertou for r in acima) / len(acima)
        if precisao >= alvo:
            intervalo = intervalo_de_wilson(sum(r.acertou for r in acima), len(acima))
            melhor = Calibracao(limiar, precisao, intervalo)
    return melhor


def intervalo_de_wilson(acertos: int, total: int, z: float = 1.96) -> tuple[float, float]:
    p = acertos / total
    denominador = 1 + z**2 / total
    centro = (p + z**2 / (2 * total)) / denominador
    margem = z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominador
    return max(0.0, centro - margem), min(1.0, centro + margem)
