import pytest

from classificacao.dominio.calibracao import Rotulo, calibrar

AMOSTRA = [
    Rotulo(pontuacao=0.99, acertou=True),
    Rotulo(pontuacao=0.95, acertou=True),
    Rotulo(pontuacao=0.90, acertou=True),
    Rotulo(pontuacao=0.80, acertou=False),
    Rotulo(pontuacao=0.70, acertou=True),
]


def test_limiar_e_a_menor_pontuacao_cuja_precisao_atinge_o_alvo():
    calibracao = calibrar(AMOSTRA, alvo=0.97)
    assert calibracao.limiar == 0.90
    assert calibracao.precisao_prevista == pytest.approx(1.0)


def test_intervalo_de_wilson_da_precisao_reflete_o_tamanho_da_amostra():
    calibracao = calibrar(AMOSTRA, alvo=0.97)
    minimo, maximo = calibracao.intervalo
    assert minimo == pytest.approx(0.4385, abs=1e-4)
    assert maximo == pytest.approx(1.0)


def test_sem_limiar_que_atinja_o_alvo_nada_e_publicado():
    amostra = [Rotulo(0.9, False), Rotulo(0.8, True)]
    assert calibrar(amostra, alvo=0.97).limiar is None


def test_amostra_vazia_e_erro():
    with pytest.raises(ValueError):
        calibrar([], alvo=0.97)
