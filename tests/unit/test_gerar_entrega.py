from classificacao.aplicacao.classificar_questao import Classificacao, Proposta
from classificacao.aplicacao.gerar_entrega import Sinais, gerar_entrega
from classificacao.dominio.calibracao import EstimativaDePrecisao
from tests.unit.test_decisao import ARVORE

ESTIMATIVA = EstimativaDePrecisao(0.97, (0.93, 0.99), limiares=(0.5, 0.6, 0.7))


def classificacao(id, a, b, juiz=None, extras_a=(), extras_b=()):
    return Classificacao(
        id,
        None if a is None else Proposta(a, 0.9, "c", extras_a),
        None if b is None else Proposta(b, 0.9, "v", extras_b),
        None if juiz is None else Proposta(juiz, 0.7, "j"),
    )


def gerar(classificacoes, ids, sinais=None, limiar=0.5, curva=lambda p: 0.96):
    return gerar_entrega(
        ids,
        {c.questao_id: c for c in classificacoes},
        ARVORE,
        sinais or {},
        limiar_de_pontuacao=limiar,
        curva=curva,
        estimativa=ESTIMATIVA,
    )


def test_concordancia_acima_do_limiar_publica_com_a_confianca_da_curva():
    entrega = gerar(
        [classificacao("Q0001", 100, 100), classificacao("Q0002", 100, 11, juiz=11)],
        ["Q0001", "Q0002"],
    )
    q1, q2 = entrega.linhas
    assert (q1["id"], q1["decisao"], q1["tema_central_id"], q1["confianca"]) == (
        "Q0001",
        "publicar",
        "100",
        "0.96",
    )
    assert (q2["decisao"], q2["tema_central_id"]) == ("revisar", "11")


def test_questao_sem_classificacao_ou_com_papel_ausente_revisa_com_a_reserva():
    entrega = gerar(
        [classificacao("Q0002", 100, None)],
        ["Q0001", "Q0002"],
        sinais={"Q0001": Sinais(reserva=11), "Q0002": Sinais(reserva=11)},
    )
    q1, q2 = entrega.linhas
    assert (q1["decisao"], q1["tema_central_id"]) == ("revisar", "11")
    assert (q2["decisao"], q2["tema_central_id"]) == ("revisar", "100")


def test_sem_limiar_calibrado_nada_e_publicado():
    entrega = gerar([classificacao("Q0001", 100, 100)], ["Q0001"], limiar=None)
    assert entrega.linhas[0]["decisao"] == "revisar"


def test_extras_sao_so_os_nos_citados_pelos_dois_e_publicaveis():
    entrega = gerar(
        [classificacao("Q0001", 100, 100, extras_a=(101, 11, 1), extras_b=(11, 1, 110))],
        ["Q0001"],
    )
    assert entrega.linhas[0]["extras_ids"] == "11"


def test_previsao_segue_o_formato_do_leia_me_com_intervalo_de_cobertura_do_bootstrap():
    estimativa = EstimativaDePrecisao(0.97, (0.93, 0.99), limiares=(0.5, 0.6, 0.9))
    entrega = gerar_entrega(
        ["Q0001", "Q0002"],
        {
            "Q0001": classificacao("Q0001", 100, 100),
            "Q0002": classificacao("Q0002", 100, 11, juiz=11),
        },
        ARVORE,
        {},
        limiar_de_pontuacao=0.5,
        curva=lambda p: 0.96,
        estimativa=estimativa,
    )
    assert entrega.previsao.splitlines()[:4] == [
        "precisao_prevista: 0.97",
        "precisao_intervalo: 0.93-0.99",
        "cobertura_prevista: 0.50",
        "cobertura_intervalo: 0.00-0.50",
    ]
