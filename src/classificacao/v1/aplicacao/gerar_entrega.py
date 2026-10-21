import math
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.calibracao import EstimativaDePrecisao, taxa_de_laplace
from classificacao.nucleo.dominio.decisao import Decisao, Resultado
from classificacao.nucleo.dominio.entrega import ItemDaEntrega, montar_entrega
from classificacao.v1.aplicacao.classificar_questao import Classificacao
from classificacao.v1.dominio.decisao import decidir
from classificacao.v1.dominio.pontuacao import pontuar


@dataclass(frozen=True)
class Sinais:
    """Sinais dos embeddings: similaridade com o nó votado e o nó mais parecido (reserva)."""

    similaridade: float = 0.0
    reserva: int | None = None


@dataclass(frozen=True)
class Entrega:
    linhas: list[dict[str, str]]
    previsao: str


def gerar_entrega(
    questoes_ids: Sequence[str],
    classificacoes: Mapping[str, Classificacao],
    arvore: Arvore,
    sinais: Mapping[str, Sinais],
    limiar_de_pontuacao: float | None,
    curva: Callable[[float], float],
    estimativa: EstimativaDePrecisao,
    rotulos: Mapping[str, int | None],
) -> Entrega:
    """`confianca` de Publicar vem da curva; a de Revisar e Fora, do acerto do mesmo motivo."""
    itens = []
    pontuacoes_publicaveis: list[float] = []
    for questao_id in questoes_ids:
        c = classificacoes.get(questao_id, Classificacao(questao_id, None, None, None))
        sinal = sinais.get(questao_id, Sinais())
        classificador, verificador, desempatador = (
            None if proposta is None else proposta.voto()
            for proposta in (c.classificador, c.verificador, c.desempatador)
        )
        pontuacao = (
            0.0
            if classificador is None or verificador is None
            else pontuar(arvore, classificador, verificador, sinal.similaridade)
        )
        resultado = decidir(
            arvore,
            classificador,
            verificador,
            desempatador,
            confianca=pontuacao,
            limiar=math.inf if limiar_de_pontuacao is None else limiar_de_pontuacao,
            reserva=sinal.reserva,
            indicios_de_injecao=c.indicios_de_injecao,
        )
        if _publicaria_com_limiar_zero(arvore, classificador, verificador, desempatador, pontuacao):
            pontuacoes_publicaveis.append(pontuacao)
        extras = _extras_em_comum(c, arvore, resultado.tema_central_id)
        itens.append(ItemDaEntrega(questao_id, resultado, extras, curva(pontuacao)))
    acertos = _acertos_na_amostra(itens, rotulos, arvore)
    itens = [_com_confianca_do_motivo(item, acertos) for item in itens]
    linhas = montar_entrega(itens, set(questoes_ids))
    publicadas = sum(item.resultado.decisao is Decisao.PUBLICAR for item in itens)
    coberturas = sorted(
        sum(p >= limiar for p in pontuacoes_publicaveis) / len(questoes_ids)
        for limiar in estimativa.limiares
    )
    previsao = _previsao(
        estimativa,
        publicadas,
        len(questoes_ids),
        coberturas,
        acertos.get((Decisao.PUBLICAR, ""), []),
    )
    return Entrega(linhas, previsao)


def _publicaria_com_limiar_zero(
    arvore: Arvore, classificador, verificador, desempatador, pontuacao
):
    # Tema duplicado e dúvida declarada nunca publicam: não entram na incerteza da cobertura.
    resultado = decidir(arvore, classificador, verificador, desempatador, pontuacao, limiar=0.0)
    return resultado.decisao is Decisao.PUBLICAR


def _acertos_na_amostra(
    itens: Sequence[ItemDaEntrega], rotulos: Mapping[str, int | None], arvore: Arvore
) -> dict[tuple[Decisao, str], list[bool]]:
    """Por (decisão, motivo): o tema central de cada Questão rotulada estava no Ramo do rótulo?"""
    acertos: dict[tuple[Decisao, str], list[bool]] = defaultdict(list)
    for item in itens:
        if item.id in rotulos:
            acertos[_chave(item.resultado)].append(
                _acertou(item.resultado, rotulos[item.id], arvore)
            )
    return acertos


def _acertou(resultado: Resultado, rotulo: int | None, arvore: Arvore) -> bool:
    if resultado.decisao is Decisao.FORA or resultado.tema_central_id is None:
        return resultado.decisao is Decisao.FORA and rotulo is None
    return rotulo is not None and arvore.mesmo_ramo(resultado.tema_central_id, rotulo)


def _chave(resultado: Resultado) -> tuple[Decisao, str]:
    return resultado.decisao, resultado.motivo


def _com_confianca_do_motivo(
    item: ItemDaEntrega, acertos: Mapping[tuple[Decisao, str], list[bool]]
) -> ItemDaEntrega:
    if item.resultado.decisao is Decisao.PUBLICAR:
        return item
    do_motivo = acertos.get(_chave(item.resultado), [])
    return replace(item, confianca=taxa_de_laplace(sum(do_motivo), len(do_motivo)))


def _previsao(
    estimativa: EstimativaDePrecisao,
    publicadas: int,
    total: int,
    coberturas: list[float],
    publicadas_na_amostra: list[bool],
) -> str:
    cobertura = publicadas / total

    def percentil(valores: list[float], q: float) -> float:
        return valores[int(q * (len(valores) - 1))] if valores else cobertura

    minimo, maximo = estimativa.intervalo
    cobertura_min, cobertura_max = percentil(coberturas, 0.025), percentil(coberturas, 0.975)
    acertos, rotuladas = sum(publicadas_na_amostra), len(publicadas_na_amostra)
    return "\n".join(
        [
            f"precisao_prevista: {estimativa.precisao:.2f}",
            f"precisao_intervalo: {minimo:.2f}-{maximo:.2f}",
            f"cobertura_prevista: {cobertura:.2f}",
            f"cobertura_intervalo: {cobertura_min:.2f}-{cobertura_max:.2f}",
            "",
            "Como chegamos nestes números",
            "",
            "Precisão. Antes de ver qualquer resultado, sorteamos uma Amostra de 50 Questões "
            "(80% entre as que podiam ser publicadas) e um agente jurídico de IA rotulou cada "
            "uma sem saber qual era o voto do pipeline (ADR 0006). Das Questões da Amostra que "
            f"esta entrega publica, {acertos} de {rotuladas} estão no Ramo do rótulo. O ponto é o "
            "menor de dois números: o bootstrap do procedimento inteiro (calibra o limiar numa "
            "reamostra e mede a precisão fora dela) e a suavização de Laplace, "
            f"({acertos}+1)/({rotuladas}+2). O intervalo junta o do bootstrap (percentis 2,5% e "
            f"97,5%) com o de Wilson para {acertos} de {rotuladas}. Sem nenhum erro na Amostra, "
            "o bootstrap sozinho diria 1,00 sem margem; Laplace e Wilson impedem isso.",
            "",
            f"Cobertura. O ponto é a fração que esta entrega publica: {publicadas} de {total}. "
            "O intervalo vem dos limiares que o bootstrap escolheu em cada reamostra: cada "
            "limiar daria uma cobertura, e ficam os percentis 2,5% e 97,5%. Só contam Questões "
            "que algum limiar publicaria; Tema duplicado e dúvida declarada nunca publicam.",
            "",
            "Por que pode estar otimista. O gabarito da Amostra é de um modelo, não da equipe "
            "de especialistas, e cada rótulo foi escolhido de uma lista de candidatos que "
            "sempre contém os Nós votados pelo pipeline. Os dois vieses puxam a precisão para "
            "cima e não estão no intervalo, que só mede o tamanho da Amostra.",
            "",
            "Coluna confianca do publicacao.csv. Em publicar, é a taxa de acerto suavizada "
            "(Laplace) da faixa de pontuação na Amostra. Em revisar e fora, é a taxa suavizada "
            "das Questões da Amostra com a mesma decisão e o mesmo motivo; sem nenhuma na "
            "Amostra, 0,50.",
            "",
        ]
    )


def _extras_em_comum(c: Classificacao, arvore: Arvore, tema_central: int | None) -> tuple[int, ...]:
    if c.classificador is None or c.verificador is None:
        return ()
    comuns = set(c.classificador.extras) & set(c.verificador.extras)
    return tuple(
        sorted(no for no in comuns if no != tema_central and arvore.pode_receber_questao(no))
    )
