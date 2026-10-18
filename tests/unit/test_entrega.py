import pytest

from classificacao.dominio.decisao import Decisao, Resultado
from classificacao.dominio.entrega import EntregaInvalida, ItemDaEntrega, montar_entrega


def publicado(id: str) -> ItemDaEntrega:
    return ItemDaEntrega(id, Resultado(Decisao.PUBLICAR, 10), extras=(100, 101), confianca=0.973)


def test_linha_publicada_segue_o_formato_do_leia_me():
    linhas = montar_entrega([publicado("Q0001")], ids_esperados={"Q0001"})
    assert linhas == [
        {
            "id": "Q0001",
            "decisao": "publicar",
            "tema_central_id": "10",
            "extras_ids": "100;101",
            "confianca": "0.97",
            "motivo": "",
        }
    ]


def test_questao_esperada_faltando_invalida_a_entrega():
    with pytest.raises(EntregaInvalida, match="Q0002"):
        montar_entrega([publicado("Q0001")], ids_esperados={"Q0001", "Q0002"})


def test_questao_duplicada_invalida_a_entrega():
    with pytest.raises(EntregaInvalida, match="Q0001"):
        montar_entrega([publicado("Q0001"), publicado("Q0001")], ids_esperados={"Q0001"})


def test_questao_nao_esperada_invalida_a_entrega():
    with pytest.raises(EntregaInvalida, match="Q9999"):
        montar_entrega([publicado("Q0001"), publicado("Q9999")], ids_esperados={"Q0001"})


@pytest.mark.parametrize(
    "resultado, confianca",
    [
        (Resultado(Decisao.PUBLICAR, None), 0.99),
        (Resultado(Decisao.REVISAR, None, "discordam"), 0.5),
        (Resultado(Decisao.REVISAR, 10, ""), 0.5),
        (Resultado(Decisao.FORA, None, ""), 0.1),
        (Resultado(Decisao.FORA, 10, "nenhum nó serve"), 0.1),
        (Resultado(Decisao.PUBLICAR, 10), 1.2),
        (Resultado(Decisao.PUBLICAR, 10), -0.1),
    ],
    ids=[
        "publicar sem tema",
        "revisar sem tema",
        "revisar sem motivo",
        "fora sem motivo",
        "fora com tema",
        "confianca acima de 1",
        "confianca abaixo de 0",
    ],
)
def test_linha_fora_das_regras_do_leia_me_invalida_a_entrega(resultado, confianca):
    item = ItemDaEntrega("Q0001", resultado, extras=(), confianca=confianca)
    with pytest.raises(EntregaInvalida, match="Q0001"):
        montar_entrega([item], ids_esperados={"Q0001"})
