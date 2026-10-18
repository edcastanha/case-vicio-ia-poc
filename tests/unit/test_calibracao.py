import pytest

from classificacao.dominio.calibracao import Rotulo, ajustar_curva, calibrar, estimar_precisao

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


def test_amostra_sem_nenhum_erro_nao_vira_previsao_de_precisao_total():
    # 40 de 40 certas: o bootstrap só reamostra acertos e diria 1,00 (1,00–1,00).
    amostra = [Rotulo(0.5 + i / 100, True) for i in range(40)]
    estimativa = estimar_precisao(amostra, alvo=0.97, repeticoes=200, semente=1)
    assert estimativa.precisao == pytest.approx(41 / 42)  # Laplace: (acertos + 1) / (n + 2)
    minimo, maximo = estimativa.intervalo
    assert minimo == pytest.approx(0.9124, abs=1e-4)  # Wilson de 40 em 40
    assert maximo == pytest.approx(1.0)


def test_com_erros_na_amostra_vale_o_bootstrap_quando_ele_e_mais_cauteloso():
    # 1 em cada 5 errada: o bootstrap fora da reamostra fica abaixo de Laplace e de Wilson.
    amostra = [Rotulo(i / 100, acertou=i % 5 != 0) for i in range(50)]
    estimativa = estimar_precisao(amostra, alvo=0.97, repeticoes=500, semente=1)
    calibracao = calibrar(amostra, alvo=0.97)
    acima = [r for r in amostra if r.pontuacao >= calibracao.limiar]
    assert estimativa.precisao < (sum(r.acertou for r in acima) + 1) / (len(acima) + 2)
    assert estimativa.intervalo[0] <= calibracao.intervalo[0]


def test_bootstrap_denuncia_o_otimismo_quando_a_pontuacao_nao_informa_o_acerto():
    # 1 em cada 5 errada, independente da pontuação: precisão real de 80%
    amostra = [Rotulo(i / 100, acertou=i % 5 != 0) for i in range(50)]
    assert calibrar(amostra, alvo=0.97).precisao_prevista == pytest.approx(1.0)
    estimativa = estimar_precisao(amostra, alvo=0.97, repeticoes=500, semente=1)
    assert estimativa.precisao < 0.9


def test_bootstrap_sem_nenhuma_publicacao_nao_tem_precisao():
    amostra = [Rotulo(0.5 + i / 100, False) for i in range(20)]
    assert estimar_precisao(amostra, alvo=0.97, repeticoes=50, semente=1) is None


def test_curva_converte_pontuacao_na_taxa_de_acerto_suavizada_da_sua_faixa():
    # faixa baixa (0.1–0.4): 1 acerto em 4 → 2/6; faixa alta (0.6–0.9): 3 em 4 → 4/6
    amostra = [
        Rotulo(0.1, False), Rotulo(0.2, False), Rotulo(0.3, True), Rotulo(0.4, False),
        Rotulo(0.6, True), Rotulo(0.7, True), Rotulo(0.8, False), Rotulo(0.9, True),
    ]  # fmt: skip
    curva = ajustar_curva(amostra, faixas=2)
    assert curva(0.25) == pytest.approx(2 / 6)
    assert curva(0.85) == pytest.approx(4 / 6)


def test_curva_nunca_diminui_quando_a_faixa_alta_acerta_menos_que_a_baixa():
    # faixa baixa: 3 em 4; faixa alta: 1 em 4 → unidas: 4 em 8 → 5/10
    amostra = [
        Rotulo(0.1, True), Rotulo(0.2, True), Rotulo(0.3, False), Rotulo(0.4, True),
        Rotulo(0.6, False), Rotulo(0.7, False), Rotulo(0.8, True), Rotulo(0.9, False),
    ]  # fmt: skip
    curva = ajustar_curva(amostra, faixas=2)
    assert curva(0.25) == pytest.approx(0.5)
    assert curva(0.85) == pytest.approx(0.5)


def test_curva_sem_nenhum_erro_nao_da_confianca_total():
    # faixas empatadas viram uma só: 10 acertos em 10 → 11/12, não 1,00 nem 6/7 por faixa
    amostra = [Rotulo(i / 10, True) for i in range(10)]
    curva = ajustar_curva(amostra, faixas=2)
    assert curva(0.1) == curva(0.9) == pytest.approx(11 / 12)


def test_bootstrap_guarda_o_limiar_de_cada_repeticao_para_a_incerteza_da_cobertura():
    amostra = [Rotulo(i / 100, acertou=i % 5 != 0) for i in range(50)]
    estimativa = estimar_precisao(amostra, alvo=0.97, repeticoes=100, semente=1)
    assert 0 < len(estimativa.limiares) <= 100
    assert len(set(estimativa.limiares)) > 1
