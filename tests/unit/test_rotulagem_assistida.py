from classificacao.aplicacao.rotulagem_assistida import conflitos

from tests.unit.test_decisao import ARVORE
from tests.unit.test_gerar_entrega import classificacao


def test_conflito_e_o_rotulo_do_modelo_fora_do_ramo_do_no_que_o_pipeline_usaria():
    classificacoes = {
        "Q0001": classificacao("Q0001", 100, 101),  # pipeline usaria o Tema 10
        "Q0002": classificacao("Q0002", 100, 100),
        "Q0003": classificacao("Q0003", 100, 100),
        "Q0004": classificacao("Q0004", None, None),  # pipeline: Fora
    }
    rotulos_do_modelo = {"Q0001": 101, "Q0002": 11, "Q0003": None, "Q0004": None}
    assert conflitos(rotulos_do_modelo, classificacoes, ARVORE) == ["Q0002", "Q0003"]


def test_no_desacordo_o_no_do_pipeline_e_a_sugestao_do_juiz():
    classificacoes = {"Q0001": classificacao("Q0001", 100, 11, juiz=11)}
    assert conflitos({"Q0001": 11}, classificacoes, ARVORE) == []
    assert conflitos({"Q0001": 100}, classificacoes, ARVORE) == ["Q0001"]
