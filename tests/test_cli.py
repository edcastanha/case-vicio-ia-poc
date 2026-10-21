import pytest

from classificacao import cli


def test_versao_desconhecida_ou_ausente_mostra_o_uso():
    for argumentos in ([], ["v9", "entrega"]):
        with pytest.raises(SystemExit, match="uso: classificacao"):
            cli.main(argumentos)


def test_repassa_o_resto_dos_argumentos_para_a_cli_da_versao(monkeypatch):
    recebidos = []
    monkeypatch.setattr("classificacao.v1.entrada.cli.main", recebidos.append)
    cli.main(["v1", "entrega", "--repeticoes", "10"])
    assert recebidos == [["entrega", "--repeticoes", "10"]]
