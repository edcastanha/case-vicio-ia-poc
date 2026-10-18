import csv

import pytest

from classificacao.adaptadores.rotulagem import RotuloInvalido, escrever_planilha, ler_rotulos
from classificacao.aplicacao.amostra_cega import ItemDeRotulagem
from classificacao.dominio.questao import Questao
from tests.unit.test_amostra_cega import ARVORE

ITEM = ItemDeRotulagem(
    Questao("Q0001", "Enunciado", "Comando", {"A": "um", "B": "dois"}, "Penal", "Ilicitude"),
    candidatos=(101, 100, 110, 11),
)


def test_planilha_mostra_questao_e_candidatos_sem_nada_dos_votos(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    escrever_planilha([ITEM], ARVORE, caminho)
    [linha] = list(csv.DictReader(caminho.open()))
    assert linha["id"] == "Q0001"
    assert "A) um" in linha["alternativas"]
    assert linha["candidato_1"] == "101 — Penal > Teoria do Crime > Culpabilidade"
    assert linha["resposta"] == ""
    assert not any("origem" in coluna or "voto" in coluna for coluna in linha)


def test_le_os_rotulos_preenchidos_incluindo_nenhum(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    escrever_planilha(
        [ITEM, ItemDeRotulagem(Questao("Q0002", "", "", {}, "", ""), (100,))],
        ARVORE,
        caminho,
    )
    linhas = list(csv.DictReader(caminho.open()))
    linhas[0]["resposta"], linhas[1]["resposta"] = "110", "Nenhum"
    with caminho.open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    assert ler_rotulos(caminho, ARVORE) == {"Q0001": 110, "Q0002": None}


def test_resposta_que_nao_e_no_nem_nenhum_e_erro_com_a_questao(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    caminho.write_text("id,resposta\nQ0007,talvez\n")
    with pytest.raises(RotuloInvalido, match="Q0007"):
        ler_rotulos(caminho, ARVORE)


def test_linha_sem_resposta_ainda_nao_foi_rotulada_e_fica_de_fora(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    caminho.write_text("id,resposta\nQ0001,100\nQ0002,\n")
    assert ler_rotulos(caminho, ARVORE) == {"Q0001": 100}


def test_resposta_colada_de_um_candidato_vale_pelo_id(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    caminho.write_text(
        "id,resposta\n"
        "Q0001,101 — Penal > Teoria do Crime > Culpabilidade\n"
        "Q0002,  110 —  Penal > Teoria da Pena > Dosimetria \n"
    )
    assert ler_rotulos(caminho, ARVORE) == {"Q0001": 101, "Q0002": 110}


def test_resposta_com_caminho_que_nao_e_o_do_id_e_erro_de_copia(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    caminho.write_text("id,resposta\nQ0003,101 — Penal > Teoria da Pena\n")
    with pytest.raises(RotuloInvalido, match="Q0003.*101"):
        ler_rotulos(caminho, ARVORE)
