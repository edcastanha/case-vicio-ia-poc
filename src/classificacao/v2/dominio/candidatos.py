"""Candidatos de uma Questão e os sinais de cada um, a partir de similaridades já calculadas."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.regua import Gabarito, certo_pela_regua
from classificacao.v2.dominio.leis import normalizar


@dataclass(frozen=True)
class Vizinha:
    """Questão da Folha-verdade parecida com a Questão classificada (nunca ela mesma)."""

    questao_id: str
    similaridade: float
    gabarito: Gabarito


@dataclass(frozen=True)
class Sinais:
    similaridade: float  # cosseno entre a Questão e o Tema enriquecido
    posicao: int  # 1 = o Nó mais parecido
    margem: float  # similaridade menos a do melhor outro Nó (negativa se não é o melhor)
    voto_das_vizinhas: float  # fração ponderada das vizinhas para quem o Nó seria certo
    lei: float  # 1 se uma lei citada aponta para o Ramo do Nó
    origem: float  # 1 se a Origem aponta para o Ramo do Nó
    termos: float  # fração dos termos do Tema enriquecido presentes na Questão
    nivel: int  # 1 Tema, 2 Subtema


def levantar_candidatos(
    arvore: Arvore,
    similaridades: Mapping[int, float],
    k: int,
    nos_das_leis: Sequence[int],
    no_da_origem: int | None,
    vizinhas: Sequence[Vizinha],
) -> list[int]:
    """Top-k por similaridade, Nós das leis, da Origem e dos Gabaritos das vizinhas.

    Os pais dos Subtemas entram também: é para lá que a decisão sobe na dúvida entre irmãos.
    """
    mais_parecidos = sorted(similaridades, key=lambda no: -similaridades[no])
    validos = [no for no in mais_parecidos if arvore.pode_receber_questao(no)][:k]
    das_vizinhas = [
        alvo
        for vizinha in vizinhas
        for alvo in (vizinha.gabarito.tema_central_id, *vizinha.gabarito.extras)
        if alvo is not None
    ]
    origem = [] if no_da_origem is None else [no_da_origem]
    candidatos = {
        no
        for no in (*validos, *nos_das_leis, *origem, *das_vizinhas)
        if arvore.pode_receber_questao(no)
    }
    pais = {arvore.no(no).pai_id for no in candidatos if arvore.no(no).nivel == 2}
    return sorted(candidatos | {pai for pai in pais if arvore.pode_receber_questao(pai)})


def sinais_do_candidato(
    arvore: Arvore,
    candidato: int,
    similaridades: Mapping[int, float],
    vizinhas: Sequence[Vizinha],
    nos_das_leis: Sequence[int],
    no_da_origem: int | None,
    termos: float,
) -> Sinais:
    propria = similaridades.get(candidato, 0.0)
    outras = [s for no, s in similaridades.items() if no != candidato]
    peso_total = sum(v.similaridade for v in vizinhas)
    voto = sum(v.similaridade for v in vizinhas if certo_pela_regua(arvore, candidato, v.gabarito))
    return Sinais(
        similaridade=propria,
        posicao=1 + sum(s > propria for s in outras),
        margem=propria - max(outras, default=0.0),
        voto_das_vizinhas=voto / peso_total if peso_total else 0.0,
        lei=float(any(arvore.mesmo_ramo(candidato, no) for no in nos_das_leis)),
        origem=float(no_da_origem is not None and arvore.mesmo_ramo(candidato, no_da_origem)),
        termos=termos,
        nivel=arvore.no(candidato).nivel,
    )


def termos_presentes(texto_da_questao: str, termos: Sequence[str]) -> float:
    if not termos:
        return 0.0
    texto = normalizar(texto_da_questao)
    achados = sum(
        bool(re.search(rf"(?<!\w){re.escape(normalizar(termo))}(?!\w)", texto)) for termo in termos
    )
    return achados / len(termos)
