import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass

from classificacao.aplicacao.portas import Cache, FalhaDoModelo, FilaDeFalhas, ModeloDeLinguagem
from classificacao.aplicacao.prompts import (
    SCHEMA_DO_VOTO,
    SISTEMA_CLASSIFICADOR,
    SISTEMA_JUIZ,
    SISTEMA_VERIFICADOR,
    disputa_para_prompt,
    questao_para_prompt,
    sistema_com_arvore,
)
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.decisao import Voto
from classificacao.dominio.questao import Questao


@dataclass(frozen=True)
class Papeis:
    classificador: ModeloDeLinguagem
    verificador: ModeloDeLinguagem
    juiz: ModeloDeLinguagem


@dataclass(frozen=True)
class Proposta:
    no_id: int | None
    confianca: float
    justificativa: str
    extras: tuple[int, ...] = ()

    def voto(self) -> Voto:
        return Voto(self.no_id, self.confianca)


@dataclass(frozen=True)
class Classificacao:
    questao_id: str
    classificador: Proposta | None
    verificador: Proposta | None
    juiz: Proposta | None


def classificar_questao(
    questao: Questao,
    arvore: Arvore,
    papeis: Papeis,
    fila_de_falhas: FilaDeFalhas,
    cache: Cache,
    tentativas: int = 3,
    esperar: Callable[[int], None] = lambda tentativa: time.sleep(2**tentativa),
) -> Classificacao:
    def votar(papel: str, modelo: ModeloDeLinguagem, sistema: str, usuario: str) -> Proposta | None:
        chave = _chave_do_cache(papel, modelo.identificador, sistema, usuario)
        if (guardada := cache.obter(chave)) is not None:
            return _ler_proposta(guardada)
        try:
            resposta = _responder_com_retry(modelo, sistema, usuario, tentativas, esperar)
            cache.guardar(chave, resposta)
            return _ler_proposta(resposta)
        except FalhaDoModelo as erro:
            fila_de_falhas.registrar(questao.id, papel, str(erro))
            return None

    classificador = votar(
        "classificador",
        papeis.classificador,
        sistema_com_arvore(SISTEMA_CLASSIFICADOR, arvore),
        questao_para_prompt(questao, com_origem=True),
    )
    verificador = votar(
        "verificador",
        papeis.verificador,
        sistema_com_arvore(SISTEMA_VERIFICADOR, arvore),
        questao_para_prompt(questao, com_origem=False),
    )
    juiz = None
    houve_desacordo = (
        classificador is not None
        and verificador is not None
        and not (classificador.no_id is None and verificador.no_id is None)
        and arvore.no_de_consenso(classificador.no_id, verificador.no_id) is None
    )
    if houve_desacordo:
        juiz = votar(
            "juiz",
            papeis.juiz,
            sistema_com_arvore(SISTEMA_JUIZ, arvore),
            disputa_para_prompt(questao, classificador, verificador),
        )
    return Classificacao(questao.id, classificador, verificador, juiz)


def _chave_do_cache(papel: str, identificador: str, sistema: str, usuario: str) -> str:
    conteudo = json.dumps([papel, identificador, sistema, usuario], ensure_ascii=False)
    return hashlib.sha256(conteudo.encode()).hexdigest()


def _responder_com_retry(
    modelo: ModeloDeLinguagem,
    sistema: str,
    usuario: str,
    tentativas: int,
    esperar: Callable[[int], None],
) -> dict:
    """Só devolve respostas que viram uma Proposta válida, para o cache guardar só essas."""
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = modelo.responder(sistema, usuario, SCHEMA_DO_VOTO)
            _ler_proposta(resposta)
            return resposta
        except FalhaDoModelo:
            if tentativa == tentativas:
                raise
            esperar(tentativa)
    raise AssertionError("inalcançável")


def _ler_proposta(resposta: dict) -> Proposta:
    try:
        return Proposta(
            resposta["no_id"],
            float(resposta["confianca"]),
            str(resposta["justificativa"]),
            tuple(int(extra) for extra in resposta["extras"]),
        )
    except (KeyError, TypeError, ValueError) as erro:
        raise FalhaDoModelo(f"resposta malformada: {erro!r}") from erro
