"""O relatorio.pdf da raiz cabe no limite do enunciado: até 5 páginas, memo incluído."""

from pathlib import Path

PDF = Path(__file__).parents[3] / "entregas/v1/relatorio.pdf"


def test_relatorio_pdf_existe_e_tem_no_maximo_5_paginas():
    dados = PDF.read_bytes()
    paginas = dados.count(b"/Type /Page") - dados.count(b"/Type /Pages")
    assert 1 <= paginas <= 5
