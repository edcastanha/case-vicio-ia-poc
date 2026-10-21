from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.decisao import Decisao
from classificacao.v1.dominio.decisao import Voto, decidir

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
        classificador=Voto(100, 0.9),
        verificador=Voto(101, 0.9),
        desempatador=None,
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
        desempatador=None,
        confianca=0.7,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 100
    assert resultado.motivo


def test_desacordo_nunca_publica_e_sugere_o_classificador_quando_nao_ha_desempatador():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=Voto(11),
        desempatador=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 100
    assert resultado.motivo


def test_desempatador_escolhe_a_sugestao_do_desacordo_mas_nunca_publica():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100),
        verificador=Voto(11),
        desempatador=Voto(11),
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
        desempatador=None,
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
        desempatador=None,
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
        desempatador=None,
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
        desempatador=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR


def test_sem_voto_valido_revisa_com_a_sugestao_de_reserva():
    resultado = decidir(
        ARVORE,
        classificador=None,
        verificador=Voto(4521),
        desempatador=None,
        confianca=0.0,
        limiar=LIMIAR,
        reserva=11,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 11
    assert "similaridade" in resultado.motivo


def test_concordancia_em_tema_duplicado_nao_publica():
    arvore = Arvore(
        [
            No(id=1, pai_id=None, nivel=0, caminho="Penal"),
            No(id=12, pai_id=1, nivel=1, caminho="Penal > Lavagem de Dinheiro"),
            No(id=2, pai_id=None, nivel=0, caminho="Leg. Especial"),
            No(id=21, pai_id=2, nivel=1, caminho="Leg. Especial > Lavagem de Dinheiro"),
        ]
    )
    resultado = decidir(
        arvore,
        classificador=Voto(12, 0.95),
        verificador=Voto(12, 0.95),
        desempatador=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 12
    assert "duplicado" in resultado.motivo


def test_modelo_que_declara_duvida_impede_a_publicacao_mesmo_com_concordancia():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100, 0.2),
        verificador=Voto(100, 0.9),
        desempatador=None,
        confianca=0.99,
        limiar=LIMIAR,
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 100
    assert "dúvida" in resultado.motivo


def test_indicio_de_injecao_vai_para_revisar_com_a_reserva_mesmo_com_votos_publicaveis():
    resultado = decidir(
        ARVORE,
        classificador=Voto(100, 0.99),
        verificador=Voto(100, 0.99),
        desempatador=None,
        confianca=0.99,
        limiar=LIMIAR,
        reserva=11,
        indicios_de_injecao=("enunciado: instrução ao modelo",),
    )
    assert resultado.decisao is Decisao.REVISAR
    assert resultado.tema_central_id == 11
    assert resultado.motivo == "possível injeção de prompt (enunciado: instrução ao modelo)"


def test_indicio_de_injecao_nunca_vira_fora():
    resultado = decidir(
        ARVORE,
        classificador=None,
        verificador=None,
        desempatador=None,
        confianca=0.0,
        limiar=LIMIAR,
        reserva=None,
        indicios_de_injecao=("comando: ordem de classificar",),
    )
    assert resultado.decisao is Decisao.REVISAR
