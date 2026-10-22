import pytest

from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.dominio.candidatos import (
    Vizinha,
    levantar_candidatos,
    sinais_do_candidato,
    termos_presentes,
)

# Penal (1) > Teoria da Pena (10) > Pena de Multa (100), Dosimetria (101)
#           > Prescrição (11)
# Leg. Especial (2) > Lei de Execução Penal (20)
ARVORE = Arvore(
    [
        No(1, None, 0, "Penal"),
        No(10, 1, 1, "Penal > Teoria da Pena", titulo="Teoria da Pena"),
        No(100, 10, 2, "Penal > Teoria da Pena > Pena de Multa", titulo="Pena de Multa"),
        No(101, 10, 2, "Penal > Teoria da Pena > Dosimetria", titulo="Dosimetria"),
        No(11, 1, 1, "Penal > Prescrição", titulo="Prescrição"),
        No(2, None, 0, "Leg. Especial"),
        No(20, 2, 1, "Leg. Especial > Lei de Execução Penal", titulo="Lei de Execução Penal"),
    ]
)
SIMILARIDADES = {10: 0.70, 100: 0.80, 101: 0.75, 11: 0.40, 20: 0.30}


def test_candidatos_juntam_top_k_lei_origem_e_vizinhas_e_sobem_ao_pai_dos_subtemas():
    candidatos = levantar_candidatos(
        ARVORE,
        SIMILARIDADES,
        k=1,
        nos_das_leis=(20,),
        no_da_origem=11,
        vizinhas=[Vizinha("Q9", 0.9, Gabarito(101))],
    )
    assert candidatos == [10, 11, 20, 100, 101]


def test_candidatos_nunca_incluem_disciplina_nem_no_desconhecido():
    candidatos = levantar_candidatos(
        ARVORE, {1: 0.99, 999: 0.98, 11: 0.5}, k=3, nos_das_leis=(2,), no_da_origem=None,
        vizinhas=[],
    )  # fmt: skip
    assert candidatos == [11]


def test_vizinha_fora_da_taxonomia_nao_traz_candidato():
    vizinhas = [Vizinha("Q9", 0.9, Gabarito(None, fora=True))]
    candidatos = levantar_candidatos(ARVORE, {11: 0.5}, 1, (), None, vizinhas)
    assert candidatos == [11]


def test_sinais_medem_similaridade_posicao_margem_e_voto_das_vizinhas_pela_regua():
    vizinhas = [Vizinha("Q8", 0.9, Gabarito(100)), Vizinha("Q9", 0.6, Gabarito(11))]
    sinais = sinais_do_candidato(
        ARVORE, 10, SIMILARIDADES, vizinhas, nos_das_leis=(), no_da_origem=None,
        termos=0.25,
    )  # fmt: skip
    assert sinais.similaridade == pytest.approx(0.70)
    assert sinais.posicao == 3  # atrás de 100 e 101
    assert sinais.margem == pytest.approx(0.70 - 0.80)
    assert sinais.voto_das_vizinhas == pytest.approx(0.9 / 1.5)  # 10 é pai do Gabarito 100
    assert sinais.termos == 0.25
    assert sinais.nivel == 1


def test_sinais_de_lei_origem_e_tema_duplicado_valem_pelo_ramo():
    sinais = sinais_do_candidato(ARVORE, 100, SIMILARIDADES, [], (10,), 10, termos=0.0)
    assert sinais.lei == 1.0  # a lei aponta o pai
    assert sinais.origem == 1.0
    assert sinais.voto_das_vizinhas == 0.0
    assert sinais_do_candidato(ARVORE, 101, SIMILARIDADES, [], (100,), None, 0.0).lei == 0.0


def test_termos_presentes_e_a_fracao_dos_termos_do_tema_que_aparecem_na_questao():
    texto = "A pena de multa e o dia-multa na dosimetria."
    assert termos_presentes(texto, ("pena de multa", "dia-multa", "sursis", "detração")) == 0.5
    assert termos_presentes(texto, ()) == 0.0
