"""Rotulagem assistida da Amostra de calibração (ADR 0004).

O Rotulador responde a amostra às cegas; o humano só arbitra os Conflitos, numa planilha com as
duas respostas em ordem sorteada, sem saber qual veio do Rotulador e qual do pipeline.
"""

import random
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from classificacao.aplicacao.classificar_questao import Classificacao, Proposta, votar_com_cache
from classificacao.aplicacao.portas import Cache, FilaDeFalhas, ModeloDeLinguagem
from classificacao.aplicacao.prompts import Prompt, questao_para_prompt
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.decisao import decidir
from classificacao.dominio.questao import Questao


@dataclass(frozen=True)
class ItemDeArbitragem:
    """O que o humano vê num Conflito: a Questão e as respostas possíveis, sem a fonte."""

    questao: Questao
    opcoes: tuple[int | None, ...]


def rotular_as_cegas(
    questoes: Sequence[Questao],
    arvore: Arvore,
    rotulador: ModeloDeLinguagem,
    prompt: Prompt,
    fila_de_falhas: FilaDeFalhas,
    cache: Cache,
    esperar: Callable[[int], None] = lambda tentativa: time.sleep(2**tentativa),
) -> dict[str, Proposta]:
    """O Rotulador vê a Questão e a Árvore, como o Verificador: sem Origem nem votos."""
    propostas = {}
    for questao in questoes:
        proposta = votar_com_cache(
            questao.id,
            "rotulador",
            rotulador,
            prompt,
            questao_para_prompt(questao, com_origem=False),
            arvore,
            fila_de_falhas,
            cache,
            esperar=esperar,
        )
        if proposta is not None:
            propostas[questao.id] = proposta
    return propostas


def no_do_pipeline(classificacao: Classificacao | None, arvore: Arvore) -> int | None:
    """O Nó que o pipeline levaria ao aluno ou ao Professor, ignorando o limiar."""
    if classificacao is None:
        return None
    classificador, verificador, juiz = (
        None if proposta is None else proposta.voto()
        for proposta in (classificacao.classificador, classificacao.verificador, classificacao.juiz)
    )
    return decidir(
        arvore, classificador, verificador, juiz, confianca=0.0, limiar=0.0
    ).tema_central_id


def conflitos(
    rotulos_do_modelo: Mapping[str, int | None],
    classificacoes: Mapping[str, Classificacao],
    arvore: Arvore,
) -> list[str]:
    """Questões em que o rótulo do Rotulador fica fora do Ramo do Nó do pipeline."""
    return sorted(
        questao_id
        for questao_id, rotulo in rotulos_do_modelo.items()
        if not _concordam(rotulo, no_do_pipeline(classificacoes.get(questao_id), arvore), arvore)
    )


def para_arbitrar(
    ids_da_amostra: Sequence[str],
    rotulos_do_modelo: Mapping[str, int | None],
    classificacoes: Mapping[str, Classificacao],
    arvore: Arvore,
) -> list[str]:
    """Conflitos e Questões sem rótulo do Rotulador (falha do provedor): o humano decide."""
    sem_rotulo = {
        questao_id for questao_id in ids_da_amostra if questao_id not in rotulos_do_modelo
    }
    return sorted(sem_rotulo | set(conflitos(rotulos_do_modelo, classificacoes, arvore)))


def itens_de_arbitragem(
    ids_em_conflito: Sequence[str],
    rotulos_do_modelo: Mapping[str, int | None],
    classificacoes: Mapping[str, Classificacao],
    questoes: Mapping[str, Questao],
    arvore: Arvore,
    semente: int,
) -> list[ItemDeArbitragem]:
    """Um item por Conflito, com as opções em ordem sorteada: a posição não revela a fonte."""
    sorteio = random.Random(semente)
    itens = []
    for questao_id in ids_em_conflito:
        opcoes = [no_do_pipeline(classificacoes.get(questao_id), arvore)]
        if questao_id in rotulos_do_modelo and _rotulo_valido(
            rotulos_do_modelo[questao_id], arvore
        ):
            opcoes.append(rotulos_do_modelo[questao_id])
        opcoes = list(dict.fromkeys(opcoes))
        sorteio.shuffle(opcoes)
        itens.append(ItemDeArbitragem(questoes[questao_id], tuple(opcoes)))
    return itens


def consolidar(
    rotulos_do_modelo: Mapping[str, int | None],
    ids_em_conflito: Sequence[str],
    escolhas: Mapping[str, int | None],
) -> dict[str, tuple[int | None, str]]:
    """Resposta de cada Questão e quem a deu; Conflito ainda sem escolha fica de fora."""
    em_conflito = set(ids_em_conflito)
    respostas = {
        questao_id: (rotulo, "rotulador")
        for questao_id, rotulo in rotulos_do_modelo.items()
        if questao_id not in em_conflito
    }
    respostas |= {
        questao_id: (escolhas[questao_id], "arbitragem")
        for questao_id in sorted(em_conflito)
        if questao_id in escolhas
    }
    return dict(sorted(respostas.items()))


def _rotulo_valido(rotulo: int | None, arvore: Arvore) -> bool:
    return rotulo is None or arvore.pode_receber_questao(rotulo)


def _concordam(rotulo: int | None, no_do_pipeline: int | None, arvore: Arvore) -> bool:
    if not _rotulo_valido(rotulo, arvore):
        return False
    if rotulo is None or no_do_pipeline is None:
        return rotulo is None and no_do_pipeline is None
    return arvore.mesmo_ramo(rotulo, no_do_pipeline)
