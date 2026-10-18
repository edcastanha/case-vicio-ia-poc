import math
import random
from collections.abc import Callable, Sequence
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


@dataclass(frozen=True)
class EstimativaDePrecisao:
    precisao: float
    intervalo: tuple[float, float]
    limiares: tuple[float, ...] = ()


def estimar_precisao(
    amostra: Sequence[Rotulo], alvo: float, repeticoes: int, semente: int
) -> EstimativaDePrecisao | None:
    """Bootstrap do procedimento inteiro: calibra numa reamostra e mede fora dela."""
    sorteio = random.Random(semente)
    acertos_total = publicadas_total = 0
    precisoes: list[float] = []
    limiares: list[float] = []
    for _ in range(repeticoes):
        indices = [sorteio.randrange(len(amostra)) for _ in amostra]
        limiar = calibrar([amostra[i] for i in indices], alvo).limiar
        sorteados = set(indices)
        fora_da_reamostra = [r for i, r in enumerate(amostra) if i not in sorteados]
        if limiar is None:
            continue
        publicadas = [r for r in fora_da_reamostra if r.pontuacao >= limiar]
        if not publicadas:
            continue
        acertos = sum(r.acertou for r in publicadas)
        acertos_total += acertos
        publicadas_total += len(publicadas)
        precisoes.append(acertos / len(publicadas))
        limiares.append(limiar)
    if not precisoes:
        return None
    precisoes.sort()
    intervalo = (
        precisoes[int(0.025 * (len(precisoes) - 1))],
        precisoes[int(0.975 * (len(precisoes) - 1))],
    )
    return EstimativaDePrecisao(acertos_total / publicadas_total, intervalo, tuple(limiares))


def ajustar_curva(amostra: Sequence[Rotulo], faixas: int) -> Callable[[float], float]:
    """Faixas com o mesmo número de rótulos; a pontuação vira a taxa de acerto da sua faixa."""
    ordenada = sorted(amostra, key=lambda r: r.pontuacao)
    tamanho = math.ceil(len(ordenada) / faixas)
    grupos = [ordenada[i : i + tamanho] for i in range(0, len(ordenada), tamanho)]
    # Une faixas vizinhas que violam a ordem (pool adjacent violators).
    blocos: list[list[Rotulo]] = []
    for grupo in grupos:
        blocos.append(list(grupo))
        while len(blocos) > 1 and _taxa(blocos[-2]) > _taxa(blocos[-1]):
            ultimo = blocos.pop()
            blocos[-1].extend(ultimo)
    limites = [(max(r.pontuacao for r in b), _taxa(b)) for b in blocos]

    def curva(pontuacao: float) -> float:
        return next((taxa for teto, taxa in limites if pontuacao <= teto), limites[-1][1])

    return curva


def _taxa(rotulos: Sequence[Rotulo]) -> float:
    return sum(r.acertou for r in rotulos) / len(rotulos)
