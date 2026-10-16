import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from classificacao.aplicacao.classificar_questao import Classificacao
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.calibracao import EstimativaDePrecisao
from classificacao.dominio.decisao import Decisao, decidir
from classificacao.dominio.entrega import ItemDaEntrega, montar_entrega
from classificacao.dominio.pontuacao import pontuar


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
) -> Entrega:
    itens = []
    pontuacoes_publicaveis: list[float] = []
    for questao_id in questoes_ids:
        c = classificacoes.get(questao_id, Classificacao(questao_id, None, None, None))
        sinal = sinais.get(questao_id, Sinais())
        classificador, verificador, juiz = (
            None if proposta is None else proposta.voto()
            for proposta in (c.classificador, c.verificador, c.juiz)
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
            juiz,
            confianca=pontuacao,
            limiar=math.inf if limiar_de_pontuacao is None else limiar_de_pontuacao,
            reserva=sinal.reserva,
        )
        if _tem_concordancia(arvore, classificador, verificador):
            pontuacoes_publicaveis.append(pontuacao)
        extras = _extras_em_comum(c, arvore, resultado.tema_central_id)
        itens.append(ItemDaEntrega(questao_id, resultado, extras, curva(pontuacao)))
    linhas = montar_entrega(itens, set(questoes_ids))
    publicadas = sum(item.resultado.decisao is Decisao.PUBLICAR for item in itens)
    coberturas = sorted(
        sum(p >= limiar for p in pontuacoes_publicaveis) / len(questoes_ids)
        for limiar in estimativa.limiares
    )
    previsao = _previsao(estimativa, publicadas / len(questoes_ids), coberturas)
    return Entrega(linhas, previsao)


def _tem_concordancia(arvore: Arvore, classificador, verificador) -> bool:
    return (
        classificador is not None
        and verificador is not None
        and arvore.no_de_consenso(classificador.no_id, verificador.no_id) is not None
    )


def _previsao(estimativa: EstimativaDePrecisao, cobertura: float, coberturas: list[float]) -> str:
    def percentil(valores: list[float], q: float) -> float:
        return valores[int(q * (len(valores) - 1))] if valores else cobertura

    minimo, maximo = estimativa.intervalo
    cobertura_min, cobertura_max = percentil(coberturas, 0.025), percentil(coberturas, 0.975)
    return "\n".join(
        [
            f"precisao_prevista: {estimativa.precisao:.2f}",
            f"precisao_intervalo: {minimo:.2f}-{maximo:.2f}",
            f"cobertura_prevista: {cobertura:.2f}",
            f"cobertura_intervalo: {cobertura_min:.2f}-{cobertura_max:.2f}",
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
