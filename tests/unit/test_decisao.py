from classificacao.dominio.arvore import Arvore, No
from classificacao.dominio.decisao import Decisao, Voto, decidir

# Penal (1) > Teoria do Crime (10) > Ilicitude (100), Culpabilidade (101)
#           > Teoria da Pena (11)
ARVORE = Arvore(
    [
        No(id=1, pai_id=None, nivel=0, caminho="Penal"),
        No(id=10, pai_id=1, nivel=1, caminho="Penal > Teoria do Crime"),
        No(id=100, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Ilicitude"),
        No(id=101, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Culpabilidade"),
        No(id=11, pai_id=1, nivel=1, caminho="Penal > Teoria da Pena"),
    ]
)
LIMIAR = 0.9


def test_concordancia_com_confianca_acima_do_limiar_publica_no_no_de_consenso():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=Voto(101),
        juiz=None,
        confianca=0.95,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.PUBLICAR
    assert resultado.tema_central_id == 10


def test_concordancia_com_confianca_abaixo_do_limiar_vai_para_revisar_com_o_consenso():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=Voto(100),
        juiz=None,
        confianca=0.7,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 100
    assert resultado.motivo


def test_desacordo_nunca_publica_e_sugere_o_classificador_quando_nao_ha_juiz():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=Voto(11),
        juiz=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 100
    assert resultado.motivo


def test_juiz_escolhe_a_sugestao_do_desacordo_mas_nunca_publica():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=Voto(11),
        juiz=Voto(11),
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 11


def test_fora_quando_classificador_e_verificador_concordam_que_nenhum_no_serve():
    resultado = decidir(
        ARVORE,
        classificador=Voto(None),
        verificador=Voto(None),
        juiz=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.FORA
    assert resultado.tema_central_id is None
    assert resultado.motivo


def test_so_um_diz_que_nenhum_no_serve_vai_para_revisar_com_o_no_do_outro():
    resultado = decidir(
        ARVORE,
        classificador=Voto(None),
        verificador=Voto(11),
        juiz=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 11


def test_falha_do_verificador_nunca_publica_com_um_voto_so():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=None,
        juiz=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 100
    assert "falha" in resultado.motivo


def test_concordancia_na_disciplina_nao_publica():
    resultado = decidir(
        ARVORE,
        classificador=Voto(1),
        verificador=Voto(1),
        juiz=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
