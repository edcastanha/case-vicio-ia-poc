import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, replace

from classificacao.aplicacao.portas import Cache, FalhaDoModelo, FilaDeFalhas, ModeloDeLinguagem
from classificacao.aplicacao.prompts import (
    SCHEMA_DO_VOTO,
    Prompt,
    PromptsDosPapeis,
    disputa_para_prompt,
    questao_para_prompt,
    sistema_com_arvore,
)
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.decisao import Voto
from classificacao.dominio.injecao import indicios_de_injecao
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
    prompt: str = ""  # rótulo da versão do prompt que gerou o voto (Prompt.rotulo)

    def voto(self) -> Voto:
        return Voto(self.no_id, self.confianca)


@dataclass(frozen=True)
class Classificacao:
    questao_id: str
    classificador: Proposta | None
    verificador: Proposta | None
    juiz: Proposta | None
    indicios_de_injecao: tuple[str, ...] = ()  # não vazio: nenhum modelo viu a Questão

    @property
    def completa(self) -> bool:
        """Os dois votos obrigatórios chegaram; incompleta é tentada de novo na próxima rodada."""
        if self.indicios_de_injecao:
            return True
        return self.classificador is not None and self.verificador is not None


def situacao(classificacao: Classificacao, arvore: Arvore) -> str:
    """Relação entre os dois votos obrigatórios: falha, fora, mesmo nó, mesmo ramo, desacordo.

    Ou "injeção", quando a Questão não foi aos modelos.
    """
    if classificacao.indicios_de_injecao:
        return "injeção"
    if classificacao.classificador is None or classificacao.verificador is None:
        return "falha"
    a, b = classificacao.classificador.no_id, classificacao.verificador.no_id
    if a is None and b is None:
        return "fora"
    if a == b and arvore.pode_receber_questao(a):
        return "mesmo no"
    if arvore.no_de_consenso(a, b) is not None:
        return "mesmo ramo"
    return "desacordo"


def classificar_questao(
    questao: Questao,
    arvore: Arvore,
    papeis: Papeis,
    prompts: PromptsDosPapeis,
    fila_de_falhas: FilaDeFalhas,
    cache: Cache,
    tentativas: int = 3,
    esperar: Callable[[int], None] = lambda tentativa: time.sleep(2**tentativa),
) -> Classificacao:
    if indicios := indicios_de_injecao(questao):
        return Classificacao(questao.id, None, None, None, indicios)

    def votar(
        papel: str, modelo: ModeloDeLinguagem, prompt: Prompt, usuario: str
    ) -> Proposta | None:
        return votar_com_cache(
            questao.id,
            papel,
            modelo,
            prompt,
            usuario,
            arvore,
            fila_de_falhas,
            cache,
            tentativas,
            esperar,
        )

    classificador = votar(
        "classificador",
        papeis.classificador,
        prompts.classificador,
        questao_para_prompt(questao, com_origem=True),
    )
    verificador = votar(
        "verificador",
        papeis.verificador,
        prompts.verificador,
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
            prompts.juiz,
            disputa_para_prompt(questao, classificador, verificador),
        )
    elif _sem_voto_valido(arvore, classificador, verificador):
        # Q42: sem embeddings, o Juiz classifica sozinho (com o prompt do Verificador)
        # para que Revisar tenha uma sugestão.
        juiz = votar(
            "juiz",
            papeis.juiz,
            prompts.verificador,
            questao_para_prompt(questao, com_origem=False),
        )
    return Classificacao(questao.id, classificador, verificador, juiz)


def votar_com_cache(
    questao_id: str,
    papel: str,
    modelo: ModeloDeLinguagem,
    prompt: Prompt,
    usuario: str,
    arvore: Arvore,
    fila_de_falhas: FilaDeFalhas,
    cache: Cache,
    tentativas: int = 3,
    esperar: Callable[[int], None] = lambda tentativa: time.sleep(2**tentativa),
) -> Proposta | None:
    """Um voto com a Árvore no system prompt, cache, retry e DLQ; None se o provedor falhou."""
    sistema = sistema_com_arvore(prompt.texto, arvore)
    chave = _chave_do_cache(papel, modelo.identificador, sistema, usuario)
    if (guardada := cache.obter(chave)) is not None:
        return replace(_ler_proposta(guardada), prompt=prompt.rotulo)
    try:
        resposta = _responder_com_retry(modelo, sistema, usuario, tentativas, esperar)
        cache.guardar(chave, resposta)
        return replace(_ler_proposta(resposta), prompt=prompt.rotulo)
    except FalhaDoModelo as erro:
        fila_de_falhas.registrar(questao_id, papel, str(erro))
        return None


def _sem_voto_valido(arvore: Arvore, *propostas: Proposta | None) -> bool:
    presentes = [p for p in propostas if p is not None]
    if presentes and all(p.no_id is None for p in presentes) and len(presentes) == 2:
        return False  # os dois dizem que nenhum nó serve: é Fora, não falta de voto
    return not any(arvore.pode_receber_questao(p.no_id) for p in presentes)


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
