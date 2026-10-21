from pathlib import Path

PDF = Path(__file__).parents[3] / "relatorio.pdf"


def test_relatorio_v2_na_raiz_cabe_em_4_paginas_mais_o_memo():
    dados = PDF.read_bytes()
    paginas = dados.count(b"/Type /Page") - dados.count(b"/Type /Pages")
    assert 1 <= paginas <= 5
