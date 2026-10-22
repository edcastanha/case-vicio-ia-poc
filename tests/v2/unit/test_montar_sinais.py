import numpy as np

from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.questao import Questao
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.aplicacao.montar_sinais import Conhecimento, Vetores, montar_sinais

ARVORE = Arvore(
    [
        No(1, None, 0, "Penal", titulo="Penal"),
        No(10, 1, 1, "Penal > Teoria da Pena", titulo="Teoria da Pena"),
        No(11, 1, 1, "Penal > Prescrição", titulo="Prescrição"),
    ]
)


def questao(id_, texto="texto"):
    return Questao(id_, texto, "", {}, "Direito Penal", "")


def conhecimento():
    # Q1 e Q2 apontam para Teoria da Pena; Q3 para Prescrição.
    q = np.array([[1.0, 0.0], [0.9, 0.1], [0.2, 1.0]])
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return Conhecimento(
        ARVORE, (), {},
        Vetores(["Q1", "Q2", "Q3"], q),
        Vetores([10, 11], np.array([[1.0, 0.0], [0.0, 1.0]])),
    )  # fmt: skip


def test_o_knn_nunca_ve_a_propria_questao_nem_as_que_nao_foram_passadas_como_rotuladas():
    rotuladas = {"Q1": Gabarito(10), "Q3": Gabarito(11)}
    sinais = montar_sinais(
        [questao("Q1"), questao("Q2")], conhecimento(), rotuladas, k=2, vizinhas=1
    )
    voto_q1 = {c.no_id: c.sinais.voto_das_vizinhas for c in sinais["Q1"]}
    voto_q2 = {c.no_id: c.sinais.voto_das_vizinhas for c in sinais["Q2"]}
    assert voto_q1 == {10: 0.0, 11: 1.0}  # a vizinha de Q1 é Q3, não ela mesma
    assert voto_q2 == {10: 1.0, 11: 0.0}  # a vizinha de Q2 é Q1


def test_similaridade_do_candidato_vem_do_produto_dos_vetores():
    sinais = montar_sinais([questao("Q3")], conhecimento(), {}, k=2)
    assert {c.no_id: round(c.sinais.similaridade, 3) for c in sinais["Q3"]} == {
        10: 0.196,
        11: 0.981,
    }
