from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.entrada.site import pagina_de_resultados

ARVORE = Arvore([No(1, None, 0, "Penal"), No(10, 1, 1, "Penal > A"), No(11, 1, 1, "Penal > B")])


def linha(id_, decisao, tema, motivo=""):
    return {
        "id": id_,
        "decisao": decisao,
        "tema_central_id": tema,
        "confianca": "0.90",
        "motivo": motivo,
    }


def test_resultados_contam_decisoes_e_marcam_certo_ou_errado_so_na_folha_verdade():
    pagina = pagina_de_resultados(
        [
            linha("Q1", "publicar", "10"),
            linha("Q2", "revisar", "11", "a|b"),
            linha("Q3", "fora", "", "militar"),
        ],
        ARVORE,
        {"Q1": Gabarito(11), "Q3": Gabarito(None, fora=True)},
    )
    assert "| publicar | 1 |" in pagina and "| fora | 1 |" in pagina
    assert "| Q1 | publicar | Penal > A | 0.90 |  | errado |" in pagina
    assert "| Q2 | revisar | Penal > B | 0.90 | a\\|b |  |" in pagina
    assert "| Q3 | fora | — | 0.90 | militar | certo |" in pagina
