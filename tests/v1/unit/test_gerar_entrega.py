from classificacao.nucleo.dominio.calibracao import EstimativaDePrecisao
from classificacao.v1.aplicacao.classificar_questao import Classificacao, Proposta
from classificacao.v1.aplicacao.gerar_entrega import Sinais, gerar_entrega
from tests.v1.unit.test_decisao import ARVORE

ESTIMATIVA = EstimativaDePrecisao(0.97, (0.93, 0.99), limiares=(0.5, 0.6, 0.7))


def classificacao(id, a, b, desempatador=None, extras_a=(), extras_b=()):
    return Classificacao(
        id,
        None if a is None else Proposta(a, 0.9, "c", extras_a),
        None if b is None else Proposta(b, 0.9, "v", extras_b),
        None if desempatador is None else Proposta(desempatador, 0.7, "j"),
    )


def gerar(classificacoes, ids, sinais=None, limiar=0.5, curva=lambda p: 0.96, rotulos=None):
    return gerar_entrega(
        ids,
        {c.questao_id: c for c in classificacoes},
        ARVORE,
        sinais or {},
        limiar_de_pontuacao=limiar,
        curva=curva,
        estimativa=ESTIMATIVA,
        rotulos=rotulos or {},
    )


def test_concordancia_acima_do_limiar_publica_com_a_confianca_da_curva():
    entrega = gerar(
        [classificacao("Q0001", 100, 100), classificacao("Q0002", 100, 11, desempatador=11)],
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
            "Q0002": classificacao("Q0002", 100, 11, desempatador=11),
        },
        ARVORE,
        {},
        limiar_de_pontuacao=0.5,
        curva=lambda p: 0.96,
        estimativa=estimativa,
        rotulos={},
    )
    assert entrega.previsao.splitlines()[:4] == [
        "precisao_prevista: 0.97",
        "precisao_intervalo: 0.93-0.99",
        "cobertura_prevista: 0.50",
        "cobertura_intervalo: 0.00-0.50",
    ]


def test_intervalo_de_cobertura_so_conta_questoes_que_algum_limiar_publicaria():
    # Q0002 concorda, mas um modelo declarou dúvida: nenhum limiar a publica
    em_duvida = Classificacao("Q0002", Proposta(100, 0.3, "c"), Proposta(100, 0.9, "v"), None)
    estimativa = EstimativaDePrecisao(0.97, (0.93, 0.99), limiares=(0.0,))
    entrega = gerar_entrega(
        ["Q0001", "Q0002"],
        {"Q0001": classificacao("Q0001", 100, 100), "Q0002": em_duvida},
        ARVORE,
        {},
        limiar_de_pontuacao=0.0,
        curva=lambda p: 0.96,
        estimativa=estimativa,
        rotulos={},
    )
    assert entrega.previsao.splitlines()[3] == "cobertura_intervalo: 0.50-0.50"


def test_confianca_fora_da_publicacao_e_o_acerto_suavizado_do_mesmo_motivo_na_amostra():
    # desacordos: a sugestão (Desempatador, 11) acertou nas 2 rotuladas → (2+1)/(2+2)
    desacordos = [classificacao(f"Q000{i}", 100, 11, desempatador=11) for i in (1, 2, 3)]
    fora = Classificacao("Q0004", Proposta(None, 0.9, "c"), Proposta(None, 0.9, "v"), None)
    entrega = gerar(
        [*desacordos, fora],
        ["Q0001", "Q0002", "Q0003", "Q0004"],
        rotulos={"Q0001": 11, "Q0002": 11},
    )
    confiancas = [(linha["decisao"], linha["confianca"]) for linha in entrega.linhas]
    assert confiancas == [
        ("revisar", "0.75"),
        ("revisar", "0.75"),
        ("revisar", "0.75"),
        ("fora", "0.50"),  # nenhum Fora na amostra: (0+1)/(0+2)
    ]


def test_previsao_explica_em_texto_livre_como_chegou_nos_numeros():
    entrega = gerar(
        [classificacao("Q0001", 100, 100), classificacao("Q0002", 100, 100)],
        ["Q0001", "Q0002"],
        rotulos={"Q0001": 100, "Q0002": 11},
    )
    explicacao = "\n".join(entrega.previsao.splitlines()[4:])
    assert "1 de 2" in explicacao  # rotuladas publicadas que estão no Ramo do rótulo
    assert "Laplace" in explicacao and "Wilson" in explicacao and "bootstrap" in explicacao
