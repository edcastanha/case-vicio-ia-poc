import csv

import pytest

from classificacao.adaptadores.rotulagem import (
    RotuloInvalido,
    escrever_planilha,
    escrever_planilha_de_arbitragem,
    ler_escolhas,
    ler_rotulos,
    preencher_respostas,
)
from classificacao.aplicacao.amostra_cega import ItemDeRotulagem
from classificacao.aplicacao.rotulagem_assistida import ItemDeArbitragem
from classificacao.dominio.questao import Questao
from tests.unit.test_amostra_cega import ARVORE


def questao(id: str) -> Questao:
    return Questao(id, "Enunciado", "Comando", {"A": "um"}, "Penal", "Ilicitude")


def escolher(caminho, escolhas: dict[str, str]) -> None:
    linhas = list(csv.DictReader(caminho.open()))
    for linha in linhas:
        linha["escolha"] = escolhas.get(linha["id"], "")
    with caminho.open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def test_planilha_de_arbitragem_mostra_opcoes_a_e_b_sem_a_fonte(tmp_path):
    caminho = tmp_path / "arbitragem.csv"
    escrever_planilha_de_arbitragem(
        [ItemDeArbitragem(questao("Q0001"), (101, None))], ARVORE, caminho
    )
    [linha] = list(csv.DictReader(caminho.open()))
    assert linha["opcao_a"] == "101 — Penal > Teoria do Crime > Culpabilidade"
    assert linha["opcao_b"] == "nenhum — nenhum nó da árvore serve"
    assert linha["escolha"] == ""
    assert not any(p in coluna for coluna in linha for p in ("rotulador", "pipeline", "origem"))


def test_escolha_pode_ser_a_b_outro_no_ou_nenhum(tmp_path):
    caminho = tmp_path / "arbitragem.csv"
    itens = [
        ItemDeArbitragem(questao(id), (101, None)) for id in ("Q0001", "Q0002", "Q0003", "Q0004")
    ]
    escrever_planilha_de_arbitragem(
        itens + [ItemDeArbitragem(questao("Q0005"), (100,))], ARVORE, caminho
    )
    escolher(caminho, {"Q0001": "a", "Q0002": "B", "Q0003": "110", "Q0004": "nenhum"})
    assert ler_escolhas(caminho, ARVORE) == {
        "Q0001": 101,
        "Q0002": None,
        "Q0003": 110,
        "Q0004": None,
    }


def test_escolha_invalida_e_erro_com_a_questao(tmp_path):
    caminho = tmp_path / "arbitragem.csv"
    escrever_planilha_de_arbitragem([ItemDeArbitragem(questao("Q0009"), (100,))], ARVORE, caminho)
    escolher(caminho, {"Q0009": "B"})  # só existe a opção A
    with pytest.raises(RotuloInvalido, match="Q0009"):
        ler_escolhas(caminho, ARVORE)


def test_preencher_respostas_nao_sobrescreve_o_que_o_humano_ja_rotulou(tmp_path):
    caminho = tmp_path / "rotulagem.csv"
    itens = [ItemDeRotulagem(questao(id), (100, 101)) for id in ("Q0001", "Q0002", "Q0003")]
    escrever_planilha(itens, ARVORE, caminho)
    linhas = list(csv.DictReader(caminho.open()))
    linhas[0]["resposta"] = "110"
    with caminho.open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    preencher_respostas(caminho, {"Q0001": (100, "rotulador"), "Q0002": (None, "arbitragem")})
    assert ler_rotulos(caminho, ARVORE) == {"Q0001": 110, "Q0002": None}
    observacoes = {linha["id"]: linha["observacao"] for linha in csv.DictReader(caminho.open())}
    assert observacoes == {"Q0001": "", "Q0002": "arbitragem", "Q0003": ""}
    assert (
        list(csv.DictReader(caminho.open()))[0]["candidato_1"]
        == "100 — Penal > Teoria do Crime > Ilicitude"
    )
