from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.v2.aplicacao.revisao_dos_temas import amostra_para_revisao


def test_amostra_comeca_pelos_temas_duplicados_e_segue_pelas_maiores_lixeiras():
    arvore = Arvore(
        [
            No(1, None, 0, "Penal"),
            No(2, None, 0, "Leg"),
            No(10, 1, 1, "Penal > LEP", titulo="LEP"),
            No(20, 2, 1, "Leg > LEP", titulo="LEP"),
            No(
                11,
                1,
                1,
                "Penal > Pena",
                titulo="Pena",
                descricao="Subtema. 453 questões no source.",
            ),
            No(
                12,
                1,
                1,
                "Penal > Vida",
                titulo="Vida",
                descricao="Subtema. 281 questões no source.",
            ),
            No(13, 1, 1, "Penal > Raro", titulo="Raro", descricao="Subtema. 3 questões no source."),
        ]
    )
    assert [no.id for no in amostra_para_revisao(arvore, tamanho=4)] == [20, 10, 11, 12]
