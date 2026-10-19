from dataclasses import dataclass
from enum import Enum

from classificacao.dominio.arvore import Arvore

# Q39: se um dos modelos diz que está em dúvida, a questão vai para o Professor.
CONFIANCA_DECLARADA_MINIMA = 0.5


class Decisao(Enum):
    PUBLICAR = "publicar"
    REVISAR = "revisar"
    FORA = "fora"


@dataclass(frozen=True)
class Voto:
    no_id: int | None
    confianca: float = 0.0


@dataclass(frozen=True)
class Resultado:
    decisao: Decisao
    tema_central_id: int | None
    motivo: str = ""


def decidir(
    arvore: Arvore,
    classificador: Voto | None,
    verificador: Voto | None,
    desempatador: Voto | None,
    confianca: float,
    limiar: float,
    reserva: int | None = None,
    indicios_de_injecao: tuple[str, ...] = (),
) -> Resultado:
    if indicios_de_injecao:
        # ADR 0005: o texto tenta instruir o modelo; vai ao Professor, nunca a Fora nem ao aluno.
        motivo = f"possível injeção de prompt ({'; '.join(indicios_de_injecao)})"
        return Resultado(Decisao.REVISAR, reserva, motivo)
    resultado = _decidir_pelos_votos(
        arvore, classificador, verificador, desempatador, confianca, limiar
    )
    if resultado.decisao is Decisao.REVISAR and resultado.tema_central_id is None:
        motivo = f"{resultado.motivo}; sem voto válido, sugestão por similaridade"
        return Resultado(Decisao.REVISAR, reserva, motivo)
    return resultado


def _decidir_pelos_votos(
    arvore: Arvore,
    classificador: Voto | None,
    verificador: Voto | None,
    desempatador: Voto | None,
    confianca: float,
    limiar: float,
) -> Resultado:
    sugestao = _primeira_sugestao_valida(arvore, desempatador, classificador, verificador)
    if classificador is None or verificador is None:
        return Resultado(Decisao.REVISAR, sugestao, "falha do provedor: só um voto disponível")
    if classificador.no_id is None and verificador.no_id is None:
        return Resultado(Decisao.FORA, None, "nenhum nó da árvore serve")
    consenso = arvore.no_de_consenso(classificador.no_id, verificador.no_id)
    if consenso is None:
        return Resultado(Decisao.REVISAR, sugestao, "classificador e verificador discordam")
    if arvore.em_tema_duplicado(consenso):
        return Resultado(Decisao.REVISAR, consenso, "tema duplicado na árvore")
    if min(classificador.confianca, verificador.confianca) < CONFIANCA_DECLARADA_MINIMA:
        return Resultado(Decisao.REVISAR, consenso, "um dos modelos declarou dúvida")
    if confianca < limiar:
        return Resultado(Decisao.REVISAR, consenso, f"confiança {confianca:.2f} abaixo do limiar")
    return Resultado(Decisao.PUBLICAR, consenso)


def _primeira_sugestao_valida(arvore: Arvore, *votos: Voto | None) -> int | None:
    return next(
        (
            voto.no_id
            for voto in votos
            if voto is not None and arvore.pode_receber_questao(voto.no_id)
        ),
        None,
    )
