"""Candidatos e sinais de cada Questão a partir dos vetores em cache (sem chamar modelo)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.questao import Questao
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.dominio.candidatos import (
    Sinais,
    Vizinha,
    levantar_candidatos,
    sinais_do_candidato,
    termos_presentes,
)
from classificacao.v2.dominio.leis import Lei, leis_citadas
from classificacao.v2.dominio.origem import no_da_origem
from classificacao.v2.dominio.temas import TemaEnriquecido
from classificacao.v2.dominio.textos import texto_da_questao


@dataclass(frozen=True)
class Vetores:
    """Embeddings normalizados: uma linha por id, na ordem de `ids`."""

    ids: Sequence
    matriz: np.ndarray

    def indice(self) -> dict:
        return {id_: i for i, id_ in enumerate(self.ids)}


@dataclass(frozen=True)
class CandidatoComSinais:
    no_id: int
    sinais: Sinais


@dataclass(frozen=True)
class Conhecimento:
    """Tudo o que o sistema sabe antes de ver uma Questão: Árvore, leis e Temas enriquecidos."""

    arvore: Arvore
    leis: Sequence[Lei]
    temas: Mapping[int, TemaEnriquecido]
    questoes: Vetores
    nos: Vetores


def montar_sinais(
    questoes: Sequence[Questao],
    conhecimento: Conhecimento,
    rotuladas: Mapping[str, Gabarito],
    k: int = 10,
    vizinhas: int = 5,
) -> dict[str, list[CandidatoComSinais]]:
    """`rotuladas` é o que o kNN pode ver: na validação cruzada, só a parte de treino."""
    c = conhecimento
    indice_q = c.questoes.indice()
    nos_por_lei = {lei.numero: lei.nos for lei in c.leis}
    ids_rotulados = [i for i in rotuladas if i in indice_q]
    matriz_rotulada = c.questoes.matriz[[indice_q[i] for i in ids_rotulados]]
    resultado = {}
    for questao in questoes:
        vetor = c.questoes.matriz[indice_q[questao.id]]
        similaridades = dict(zip(c.nos.ids, (c.nos.matriz @ vetor).tolist(), strict=True))
        proximas = _vizinhas(questao.id, vetor, ids_rotulados, matriz_rotulada, rotuladas, vizinhas)
        texto = texto_da_questao(questao)
        nos_das_leis = tuple(
            no for numero in leis_citadas(texto, c.leis) for no in nos_por_lei.get(numero, ())
        )
        origem = no_da_origem(c.arvore, questao.disciplina_origem, questao.assunto_origem)
        candidatos = levantar_candidatos(c.arvore, similaridades, k, nos_das_leis, origem, proximas)
        resultado[questao.id] = [
            CandidatoComSinais(
                no,
                sinais_do_candidato(
                    c.arvore, no, similaridades, proximas, nos_das_leis, origem,
                    termos_presentes(texto, c.temas[no].termos if no in c.temas else ()),
                ),
            )
            for no in candidatos
        ]  # fmt: skip
    return resultado


def _vizinhas(questao_id, vetor, ids_rotulados, matriz_rotulada, rotuladas, quantas):
    if not ids_rotulados:
        return []
    similaridades = matriz_rotulada @ vetor
    ordem = np.argsort(-similaridades)
    escolhidas = [i for i in ordem if ids_rotulados[i] != questao_id][:quantas]
    return [
        Vizinha(ids_rotulados[i], float(similaridades[i]), rotuladas[ids_rotulados[i]])
        for i in escolhidas
    ]
