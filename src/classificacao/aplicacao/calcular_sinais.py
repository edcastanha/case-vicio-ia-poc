from collections.abc import Mapping, Sequence

import numpy as np

from classificacao.aplicacao.classificar_questao import Classificacao
from classificacao.aplicacao.gerar_entrega import Sinais
from classificacao.aplicacao.portas import Embeddings
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.questao import Questao


def calcular_sinais(
    questoes: Sequence[Questao],
    arvore: Arvore,
    classificacoes: Mapping[str, Classificacao],
    embeddings: Embeddings,
    lote: int = 100,
) -> dict[str, Sinais]:
    """Similaridade com o nó que seria publicado e o nó mais parecido (reserva)."""
    nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.id)
    vetores_nos = _normalizar(_vetorizar(embeddings, [no.caminho for no in nos], lote))
    vetores_questoes = _normalizar(_vetorizar(embeddings, [_texto(q) for q in questoes], lote))
    similaridades = vetores_questoes @ vetores_nos.T
    indice = {no.id: i for i, no in enumerate(nos)}
    sinais = {}
    for linha, questao in zip(similaridades, questoes, strict=True):
        no_votado = _no_votado(classificacoes.get(questao.id), arvore)
        similaridade = float(linha[indice[no_votado]]) if no_votado in indice else 0.0
        sinais[questao.id] = Sinais(
            similaridade=max(0.0, similaridade), reserva=nos[int(np.argmax(linha))].id
        )
    return sinais


def _no_votado(c: Classificacao | None, arvore: Arvore) -> int | None:
    if c is None or c.classificador is None:
        return None
    if c.verificador is not None:
        consenso = arvore.no_de_consenso(c.classificador.no_id, c.verificador.no_id)
        if consenso is not None:
            return consenso
    return c.classificador.no_id


def _texto(questao: Questao) -> str:
    alternativas = "\n".join(f"{letra}) {texto}" for letra, texto in questao.alternativas.items())
    return "\n".join(parte for parte in (questao.enunciado, questao.comando, alternativas) if parte)


def _vetorizar(embeddings: Embeddings, textos: list[str], lote: int) -> np.ndarray:
    vetores = []
    for inicio in range(0, len(textos), lote):
        vetores.extend(embeddings.vetorizar(textos[inicio : inicio + lote]))
    return np.array(vetores, dtype=float)


def _normalizar(vetores: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(vetores, axis=1, keepdims=True)
    return vetores / np.where(normas == 0, 1, normas)
