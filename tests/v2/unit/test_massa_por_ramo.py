import pytest

from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.v2.dominio.ramo import massa_por_ramo

# Penal (1) > Teoria da Pena (10) > Multa (100), Dosimetria (101); > Prescrição (11)
ARVORE = Arvore(
    [
        No(1, None, 0, "Penal"),
        No(10, 1, 1, "Penal > Teoria da Pena"),
        No(100, 10, 2, "Penal > Teoria da Pena > Multa"),
        No(101, 10, 2, "Penal > Teoria da Pena > Dosimetria"),
        No(11, 1, 1, "Penal > Prescrição"),
    ]
)


def test_o_tema_pai_soma_a_massa_dos_subtemas_e_cada_subtema_soma_a_do_pai():
    # a chance de o Gabarito ser cada Nó, antes de normalizar
    massa = massa_por_ramo(ARVORE, [10, 100, 101, 11], [0.1, 0.3, 0.3, 0.2])
    assert massa == pytest.approx([0.7 / 0.9, 0.4 / 0.9, 0.4 / 0.9, 0.2 / 0.9])


def test_sem_nenhuma_chance_a_massa_e_zero():
    assert massa_por_ramo(ARVORE, [10, 11], [0.0, 0.0]) == [0.0, 0.0]
