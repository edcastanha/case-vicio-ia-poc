import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from classificacao.aplicacao.classificar_questao import Classificacao
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.questao import Questao

_MINIMO_DE_CANDIDATOS = 4
_FRACAO_COM_CONCORDANCIA = 0.8


@dataclass(frozen=True)
class ItemDeRotulagem:
    """O que o rotulador vê: a questão e candidatos embaralhados, nada sobre os votos."""

    questao: Questao
    candidatos: tuple[int, ...]


def gerar_amostra_cega(
    classificacoes: Sequence[Classificacao],
    questoes: Mapping[str, Questao],
    arvore: Arvore,
    n: int,
    semente: int,
) -> list[ItemDeRotulagem]:
    """80% sorteado uniformemente entre as publicáveis (estimativa sem viés da precisão),
    o resto entre desacordos, Fora e falhas (diagnóstico)."""
    sorteio = random.Random(semente)
    ordenadas = sorted(classificacoes, key=lambda c: c.questao_id)
    com_concordancia = [c for c in ordenadas if _tem_concordancia(c, arvore)]
    demais = [c for c in ordenadas if not _tem_concordancia(c, arvore)]
    quantas_demais = min(
        len(demais), n - min(len(com_concordancia), round(n * _FRACAO_COM_CONCORDANCIA))
    )
    escolhidas = sorteio.sample(demais, quantas_demais)
    escolhidas += sorteio.sample(com_concordancia, n - quantas_demais)
    escolhidas.sort(key=lambda c: c.questao_id)
    return [
        ItemDeRotulagem(questoes[c.questao_id], _candidatos(c, arvore, sorteio)) for c in escolhidas
    ]


def _candidatos(
    classificacao: Classificacao, arvore: Arvore, sorteio: random.Random
) -> tuple[int, ...]:
    """Nós votados + vizinhos na árvore (distratores difíceis) + nós ao acaso, embaralhados."""
    votados = {
        proposta.no_id
        for proposta in (classificacao.classificador, classificacao.verificador, classificacao.juiz)
        if proposta is not None and arvore.pode_receber_questao(proposta.no_id)
    }
    publicaveis = sorted(no.id for no in arvore.nos_que_podem_receber_questao())
    vizinhos = sorted(n for v in votados for n in publicaveis if _vizinhos(arvore, v, n))
    candidatos = set(votados)
    for fonte in (vizinhos, publicaveis):
        disponiveis = [n for n in fonte if n not in candidatos]
        sorteio.shuffle(disponiveis)
        candidatos.update(disponiveis[: max(0, _MINIMO_DE_CANDIDATOS - len(candidatos))])
    embaralhados = sorted(candidatos)
    sorteio.shuffle(embaralhados)
    return tuple(embaralhados)


def _vizinhos(arvore: Arvore, a: int, b: int) -> bool:
    no_a, no_b = arvore.no(a), arvore.no(b)
    return a != b and (no_a.pai_id == no_b.pai_id or no_a.pai_id == b or no_b.pai_id == a)


def _tem_concordancia(classificacao: Classificacao, arvore: Arvore) -> bool:
    c, v = classificacao.classificador, classificacao.verificador
    return c is not None and v is not None and arvore.no_de_consenso(c.no_id, v.no_id) is not None
