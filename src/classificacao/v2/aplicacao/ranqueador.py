"""O Ranqueador: dá a cada Candidato a probabilidade de estar certo pela Régua."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.regua import Gabarito, certo_pela_regua
from classificacao.v2.aplicacao.montar_sinais import CandidatoComSinais
from classificacao.v2.dominio.ramo import massa_por_ramo

NOMES_DAS_FEATURES = (
    "similaridade",
    "inverso_da_posicao",
    "margem",
    "voto_das_vizinhas",
    "lei",
    "origem",
    "termos",
    "subtema",
    "tema_duplicado",
    "fatia_parte",
    "similaridade_maxima_da_questao",
)


def features(arvore: Arvore, candidatos: Sequence[CandidatoComSinais]) -> np.ndarray:
    maxima = max((c.sinais.similaridade for c in candidatos), default=0.0)
    return np.array(
        [
            [
                c.sinais.similaridade,
                1.0 / c.sinais.posicao,
                c.sinais.margem,
                c.sinais.voto_das_vizinhas,
                c.sinais.lei,
                c.sinais.origem,
                c.sinais.termos,
                float(c.sinais.nivel == 2),
                float(arvore.em_tema_duplicado(c.no_id)),
                float("(parte" in arvore.no(c.no_id).titulo.casefold()),
                maxima,
            ]
            for c in candidatos
        ]
    ).reshape(-1, len(NOMES_DAS_FEATURES))


@dataclass(frozen=True)
class Escolha:
    """O melhor Candidato de uma Questão e a pontuação que o Ranqueador deu a ele."""

    no_id: int | None
    pontuacao: float


class Ranqueador:
    """Tipos comparados no ticket 08: similaridade, knn, logistica, mlp e ramo.

    `ramo` aprende a chance de cada Candidato ser o próprio Gabarito (Tema central ou Extra) e
    pontua cada um pela massa do seu Ramo (dominio/ramo.py). Os outros aprendem direto "certo
    pela Régua", e o Nó pai e o filho viram exemplos positivos ao mesmo tempo.
    """

    def __init__(self, tipo: str, semente: int = 0) -> None:
        self.tipo = tipo
        self._modelo = {
            "ramo": lambda: make_pipeline(
                StandardScaler(), LogisticRegression(C=1.0, max_iter=3000)
            ),
            "logistica": lambda: make_pipeline(
                StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)
            ),
            "mlp": lambda: make_pipeline(
                StandardScaler(),
                MLPClassifier(
                    hidden_layer_sizes=(16,), alpha=1e-2, max_iter=3000, random_state=semente
                ),
            ),
        }.get(tipo, lambda: None)()

    def treinar(
        self,
        arvore: Arvore,
        sinais: Mapping[str, Sequence[CandidatoComSinais]],
        gabaritos: Mapping[str, Gabarito],
    ) -> "Ranqueador":
        if self._modelo is None:
            return self
        linhas, rotulos = [], []
        for questao_id, candidatos in sinais.items():
            if candidatos:
                linhas.append(features(arvore, candidatos))
                gabarito = gabaritos[questao_id]
                rotulos += [self._rotulo(arvore, c.no_id, gabarito) for c in candidatos]
        self._modelo.fit(np.vstack(linhas), np.array(rotulos, dtype=int))
        return self

    def pontuar(self, arvore: Arvore, candidatos: Sequence[CandidatoComSinais]) -> np.ndarray:
        if not candidatos:
            return np.array([])
        if self.tipo == "similaridade":
            return np.array([c.sinais.similaridade for c in candidatos])
        if self.tipo == "knn":
            # desempate pela similaridade, que nunca alcança um ponto de voto
            return np.array(
                [c.sinais.voto_das_vizinhas + 1e-3 * c.sinais.similaridade for c in candidatos]
            )
        chances = self._modelo.predict_proba(features(arvore, candidatos))[:, 1]
        if self.tipo == "ramo":
            return np.array(massa_por_ramo(arvore, [c.no_id for c in candidatos], chances))
        return chances

    def _rotulo(self, arvore: Arvore, no_id: int, gabarito: Gabarito) -> bool:
        if self.tipo == "ramo":
            return no_id == gabarito.tema_central_id or no_id in gabarito.extras
        return certo_pela_regua(arvore, no_id, gabarito)

    def escolher(self, arvore: Arvore, candidatos: Sequence[CandidatoComSinais]) -> Escolha:
        pontuacoes = self.pontuar(arvore, candidatos)
        if not len(pontuacoes):
            return Escolha(None, 0.0)
        melhor = int(np.argmax(pontuacoes))
        return Escolha(candidatos[melhor].no_id, float(pontuacoes[melhor]))
