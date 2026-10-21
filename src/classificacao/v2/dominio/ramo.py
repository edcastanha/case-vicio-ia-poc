from collections.abc import Sequence

from classificacao.nucleo.dominio.arvore import Arvore


def massa_por_ramo(arvore: Arvore, nos: Sequence[int], chances: Sequence[float]) -> list[float]:
    """Chance de cada Nó estar certo pela Régua, dadas as chances de cada um ser o Gabarito.

    Publicar num Nó acerta se o Gabarito está no Ramo dele, então a chance de acertar é a soma
    das chances normalizadas dos Nós do mesmo Ramo. O Tema pai junta as dos seus Subtemas, e
    por isso a dúvida entre irmãos sobe para o pai sem regra especial.
    """
    total = sum(chances)
    if total <= 0:
        return [0.0 for _ in nos]
    return [
        sum(c for outro, c in zip(nos, chances, strict=True) if arvore.mesmo_ramo(no, outro))
        / total
        for no in nos
    ]
