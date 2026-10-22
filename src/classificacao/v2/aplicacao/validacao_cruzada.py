"""Validação cruzada na Folha-verdade: toda Questão é pontuada por um Ranqueador que não a viu."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from sklearn.model_selection import StratifiedKFold

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.calibracao import Rotulo, limiar_por_laplace, taxa_de_laplace
from classificacao.nucleo.dominio.questao import Questao
from classificacao.nucleo.dominio.regua import Gabarito, certo_pela_regua
from classificacao.v2.aplicacao.montar_sinais import CandidatoComSinais
from classificacao.v2.aplicacao.ranqueador import Ranqueador

# montar(questoes, rotuladas) -> sinais; o kNN só pode ver `rotuladas`.
Montar = Callable[[Sequence[Questao], Mapping[str, Gabarito]], dict[str, list[CandidatoComSinais]]]


@dataclass(frozen=True)
class ForaDoFold:
    questao_id: str
    no_id: int | None
    pontuacao: float
    acertou: bool


@dataclass(frozen=True)
class Resultado:
    tipo: str
    previsoes: list[ForaDoFold]
    limiar: float | None
    publicadas: int
    acertos: int

    @property
    def cobertura(self) -> float:
        return self.publicadas / len(self.previsoes)

    @property
    def precisao_suavizada(self) -> float:
        return taxa_de_laplace(self.acertos, self.publicadas)


def estrato(gabarito: Gabarito, arvore: Arvore) -> str:
    """Disciplina do Tema central, ou "fora": a mesma mistura em todo fold."""
    if gabarito.fora or gabarito.tema_central_id is None:
        return "fora"
    return arvore.no(gabarito.tema_central_id).caminho.split(" > ")[0]


def validar(
    tipo: str,
    arvore: Arvore,
    questoes: Mapping[str, Questao],
    folha: Mapping[str, Gabarito],
    montar: Montar,
    alvo: float,
    folds: int = 10,
    semente: int = 0,
) -> Resultado:
    ids = sorted(folha)
    estratos = [estrato(folha[i], arvore) for i in ids]
    divisor = StratifiedKFold(n_splits=folds, shuffle=True, random_state=semente)
    previsoes = []
    for treino, teste in divisor.split(ids, estratos):
        rotuladas = {ids[i]: folha[ids[i]] for i in treino}
        sinais_treino = montar([questoes[i] for i in rotuladas], rotuladas)
        ranqueador = Ranqueador(tipo, semente).treinar(arvore, sinais_treino, rotuladas)
        ids_teste = [ids[i] for i in teste]
        sinais_teste = montar([questoes[i] for i in ids_teste], rotuladas)
        for questao_id in ids_teste:
            escolha = ranqueador.escolher(arvore, sinais_teste[questao_id])
            acertou = escolha.no_id is not None and certo_pela_regua(
                arvore, escolha.no_id, folha[questao_id]
            )
            previsoes.append(ForaDoFold(questao_id, escolha.no_id, escolha.pontuacao, acertou))
    rotulos = [Rotulo(p.pontuacao, p.acertou) for p in previsoes]
    limiar = limiar_por_laplace(rotulos, alvo)
    acima = [r for r in rotulos if limiar is not None and r.pontuacao >= limiar]
    return Resultado(tipo, previsoes, limiar, len(acima), sum(r.acertou for r in acima))
