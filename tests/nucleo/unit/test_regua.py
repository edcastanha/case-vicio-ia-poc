from classificacao.nucleo.dominio.regua import Gabarito, certo_pela_regua
from tests.nucleo.unit.test_arvore import arvore

# Penal (1) > Teoria do Crime (10) > Ilicitude (100), Culpabilidade (101)
#           > Teoria da Pena (11)


def test_publicar_no_tema_central_ou_num_no_do_mesmo_ramo_e_certo():
    gabarito = Gabarito(tema_central_id=100)
    assert certo_pela_regua(arvore(), 100, gabarito)
    assert certo_pela_regua(arvore(), 10, gabarito)  # o pai


def test_publicar_num_subtema_irmao_do_tema_central_e_erro():
    assert not certo_pela_regua(arvore(), 101, Gabarito(tema_central_id=100))


def test_publicar_num_extra_ou_no_ramo_de_um_extra_e_certo():
    gabarito = Gabarito(tema_central_id=11, extras=(100,))
    assert certo_pela_regua(arvore(), 100, gabarito)
    assert certo_pela_regua(arvore(), 10, gabarito)
    assert not certo_pela_regua(arvore(), 101, gabarito)


def test_publicar_uma_questao_fora_da_taxonomia_e_sempre_erro():
    assert not certo_pela_regua(arvore(), 100, Gabarito(tema_central_id=None, fora=True))


def test_no_que_nao_existe_na_arvore_e_erro():
    assert not certo_pela_regua(arvore(), 999, Gabarito(tema_central_id=100))
