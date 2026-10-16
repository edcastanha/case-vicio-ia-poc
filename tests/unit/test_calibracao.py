import pytest

from classificacao.dominio.calibracao import Rotulo, calibrar, estimar_precisao

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


def test_bootstrap_de_amostra_toda_correta_preve_precisao_total():
    amostra = [Rotulo(0.5 + i / 100, True) for i in range(40)]
    estimativa = estimar_precisao(amostra, alvo=0.97, repeticoes=200, semente=1)
    assert estimativa.precisao == pytest.approx(1.0)
    assert estimativa.intervalo == pytest.approx((1.0, 1.0))


def test_bootstrap_denuncia_o_otimismo_quando_a_pontuacao_nao_informa_o_acerto():
    # 1 em cada 5 errada, independente da pontuação: precisão real de 80%
    amostra = [Rotulo(i / 100, acertou=i % 5 != 0) for i in range(50)]
    assert calibrar(amostra, alvo=0.97).precisao_prevista == pytest.approx(1.0)
    estimativa = estimar_precisao(amostra, alvo=0.97, repeticoes=500, semente=1)
    assert estimativa.precisao < 0.9


def test_bootstrap_sem_nenhuma_publicacao_nao_tem_precisao():
    amostra = [Rotulo(0.5 + i / 100, False) for i in range(20)]
    assert estimar_precisao(amostra, alvo=0.97, repeticoes=50, semente=1) is None
