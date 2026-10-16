from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from classificacao.dominio.decisao import Decisao, Resultado


class EntregaInvalida(ValueError):
    pass


@dataclass(frozen=True)
class ItemDaEntrega:
    id: str
    resultado: Resultado
    extras: tuple[int, ...]
    confianca: float


def montar_entrega(itens: Sequence[ItemDaEntrega], ids_esperados: set[str]) -> list[dict[str, str]]:
    problemas = _problemas_de_completude(itens, ids_esperados)
    problemas += [f"{item.id}: {p}" for item in itens for p in _problemas_da_linha(item)]
    if problemas:
        raise EntregaInvalida("; ".join(problemas))
    return [_linha(item) for item in itens]


def _problemas_de_completude(itens: Sequence[ItemDaEntrega], ids_esperados: set[str]) -> list[str]:
    contagem = Counter(item.id for item in itens)
    faltando = sorted(ids_esperados - contagem.keys())
    duplicadas = sorted(id for id, n in contagem.items() if n > 1)
    inesperadas = sorted(contagem.keys() - ids_esperados)
    return [
        f"{rotulo}: {', '.join(ids)}"
        for rotulo, ids in (
            ("faltando", faltando),
            ("duplicadas", duplicadas),
            ("não esperadas", inesperadas),
        )
        if ids
    ]


def _problemas_da_linha(item: ItemDaEntrega) -> list[str]:
    decisao, tema, motivo = (
        item.resultado.decisao,
        item.resultado.tema_central_id,
        item.resultado.motivo,
    )
    regras = [
        (decisao is not Decisao.FORA and tema is None, f"{decisao.value} exige tema central"),
        (decisao is Decisao.FORA and tema is not None, "fora não pode ter tema central"),
        (decisao is not Decisao.PUBLICAR and not motivo, f"{decisao.value} exige motivo"),
        (not 0 <= item.confianca <= 1, f"confiança {item.confianca} fora de [0, 1]"),
    ]
    return [mensagem for violada, mensagem in regras if violada]


def _linha(item: ItemDaEntrega) -> dict[str, str]:
    tema = item.resultado.tema_central_id
    return {
        "id": item.id,
        "decisao": item.resultado.decisao.value,
        "tema_central_id": "" if tema is None else str(tema),
        "extras_ids": ";".join(str(extra) for extra in item.extras),
        "confianca": f"{item.confianca:.2f}",
        "motivo": item.resultado.motivo,
    }
