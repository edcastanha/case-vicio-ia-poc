from classificacao.aplicacao.calibrar_com_rotulos import rotulos_de_calibracao
from tests.unit.test_decisao import ARVORE
from tests.unit.test_gerar_entrega import classificacao


def calibrar(classificacoes, rotulos):
    return rotulos_de_calibracao(
        {c.questao_id: c for c in classificacoes}, rotulos, ARVORE, sinais={}
    )


def test_questao_publicavel_acerta_quando_o_rotulo_esta_no_mesmo_ramo_do_no_publicado():
    # consenso entre 100 e 101 é o Tema 10; rótulo 101 é filho de 10: acerto
    [rotulo] = calibrar([classificacao("Q0001", 100, 101)], {"Q0001": 101})
    assert rotulo.acertou
    assert 0 < rotulo.pontuacao < 1


def test_rotulo_em_outro_ramo_ou_nenhum_e_erro():
    resultado = calibrar(
        [classificacao("Q0001", 100, 100), classificacao("Q0002", 100, 100)],
        {"Q0001": 11, "Q0002": None},
    )
    assert [r.acertou for r in resultado] == [False, False]


def test_so_entram_questoes_publicaveis_e_rotuladas():
    resultado = calibrar(
        [
            classificacao("Q0001", 100, 11, desempatador=11),  # desacordo: nunca publica
            classificacao("Q0002", 100, 100),  # sem rótulo
            classificacao("Q0003", 100, 100),
        ],
        {"Q0001": 11, "Q0003": 100},
    )
    assert len(resultado) == 1
