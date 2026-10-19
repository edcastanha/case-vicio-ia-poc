"""Rotulador: segunda opinião sobre a Amostra de calibração, às cegas (ADR 0006).

Não gera rótulo: mede quantas vezes um modelo fora do pipeline cai no Ramo da Amostra.
"""

import time
from collections.abc import Callable, Mapping, Sequence

from classificacao.aplicacao.classificar_questao import Classificacao, Proposta, votar_com_cache
from classificacao.aplicacao.portas import Cache, FilaDeFalhas, ModeloDeLinguagem
from classificacao.aplicacao.prompts import Prompt, questao_para_prompt
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.decisao import decidir
from classificacao.dominio.injecao import indicios_de_injecao
from classificacao.dominio.questao import Questao


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
        if indicios_de_injecao(questao):
            continue  # ADR 0005: o texto não vai a nenhum modelo
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
    classificador, verificador, desempatador = (
        None if proposta is None else proposta.voto()
        for proposta in (
            classificacao.classificador,
            classificacao.verificador,
            classificacao.desempatador,
        )
    )
    return decidir(
        arvore, classificador, verificador, desempatador, confianca=0.0, limiar=0.0
    ).tema_central_id


def divergencias(
    rotulos_do_modelo: Mapping[str, int | None],
    rotulos: Mapping[str, int | None],
    arvore: Arvore,
) -> list[str]:
    """Questões da Amostra em que o Rotulador fica fora do Ramo do rótulo da Amostra."""
    return sorted(
        questao_id
        for questao_id, rotulo in rotulos.items()
        if questao_id in rotulos_do_modelo
        and not _mesmo_ramo(rotulos_do_modelo[questao_id], rotulo, arvore)
    )


def _mesmo_ramo(a: int | None, b: int | None, arvore: Arvore) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return arvore.pode_receber_questao(a) and arvore.mesmo_ramo(a, b)
