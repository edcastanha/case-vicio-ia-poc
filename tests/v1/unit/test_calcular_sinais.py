import pytest

from classificacao.nucleo.dominio.questao import Questao
from classificacao.v1.aplicacao.calcular_sinais import calcular_sinais
from tests.v1.unit.test_decisao import ARVORE
from tests.v1.unit.test_gerar_entrega import classificacao

# Vetores à mão: cada nó aponta numa direção; a questão aponta para Ilicitude (100).
VETORES = {
    "Penal > Teoria do Crime": [1.0, 0.0, 0.0],
    "Penal > Teoria do Crime > Ilicitude": [0.0, 1.0, 0.0],
    "Penal > Teoria do Crime > Culpabilidade": [0.0, 0.0, 1.0],
    "Penal > Teoria da Pena": [-1.0, 0.0, 0.0],
    "legítima defesa": [0.0, 1.0, 0.0],
}


class EmbeddingsFake:
    def __init__(self):
        self.chamadas = 0

    def vetorizar(self, textos):
        self.chamadas += 1
        return [VETORES.get(t) or next(v for k, v in VETORES.items() if k in t) for t in textos]


QUESTAO = Questao("Q0001", "legítima defesa", "", {}, "", "")


def test_reserva_e_o_no_publicavel_mais_parecido_com_a_questao():
    sinais = calcular_sinais([QUESTAO], ARVORE, {}, EmbeddingsFake())
    assert sinais["Q0001"].reserva == 100


def test_similaridade_e_o_cosseno_entre_a_questao_e_o_no_que_seria_publicado():
    votos = {"Q0001": classificacao("Q0001", 100, 100)}
    sinais = calcular_sinais([QUESTAO], ARVORE, votos, EmbeddingsFake())
    assert sinais["Q0001"].similaridade == pytest.approx(1.0)
    votos = {"Q0001": classificacao("Q0001", 101, 101)}
    sinais = calcular_sinais([QUESTAO], ARVORE, votos, EmbeddingsFake())
    assert sinais["Q0001"].similaridade == pytest.approx(0.0)


def test_similaridade_negativa_vira_zero_para_ficar_entre_0_e_1():
    votos = {"Q0001": classificacao("Q0001", 11, 11)}
    sinais = calcular_sinais(
        [Questao("Q0001", "Penal > Teoria do Crime", "", {}, "", "")],
        ARVORE,
        votos,
        EmbeddingsFake(),
    )
    assert sinais["Q0001"].similaridade == 0.0
