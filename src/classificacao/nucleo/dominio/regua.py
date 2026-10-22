from dataclasses import dataclass

from classificacao.nucleo.dominio.arvore import Arvore


@dataclass(frozen=True)
class Gabarito:
    """O que a equipe atribuiu a uma Questão: Tema central, Extras ou Fora."""

    tema_central_id: int | None
    extras: tuple[int, ...] = ()
    fora: bool = False


def certo_pela_regua(arvore: Arvore, publicado: int, gabarito: Gabarito) -> bool:
    """Certo é o Ramo do Tema central ou de um Extra; Subtema irmão e Fora são erro."""
    if gabarito.fora:
        return False
    alvos = (gabarito.tema_central_id, *gabarito.extras)
    return any(alvo is not None and arvore.mesmo_ramo(publicado, alvo) for alvo in alvos)
