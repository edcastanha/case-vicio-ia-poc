"""Gera o PDF do relatório de uma versão, com o memo ao Professor na última página.

Uso: uv run python scripts/gerar_relatorio_pdf.py {v1,v2} [caminho do Chrome ou Chromium]
A v2 grava relatorio.pdf na raiz (a entrega vigente); a v1, entregas/v1/relatorio.pdf.
Sem o caminho, usa a variável CHROME ou procura chromium/google-chrome no PATH.
"""

import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

RAIZ = Path(__file__).parents[1]
REPOSITORIO = "https://github.com/edcastanha/case-vicio-ia-poc"
_LINK = re.compile(r"\]\(([^)\s]+)\)")

ESTILO = """
@page {
  size: A4;
  margin: 2cm 2cm 1.6cm;
  @bottom-center { content: counter(page) " / " counter(pages); font: 9pt sans-serif; color: #666; }
}
body { font: 11pt/1.35 "Inter", "Helvetica Neue", Arial, sans-serif; color: #111; }
h1 { font-size: 16pt; margin: 0 0 6pt; }
h2 { font-size: 13pt; margin: 10pt 0 4pt; }
p, li { margin: 3pt 0; }
a { color: #1a4fbf; text-decoration: none; }
code { font-size: 9.5pt; }
table { border-collapse: collapse; font-size: 10pt; margin: 4pt 0; }
td, th { border: 1px solid #999; padding: 2px 5px; vertical-align: top; }
.memo { page-break-before: always; }
"""


def _links_para_o_github(texto: str, origem: str) -> str:
    def trocar(encontrado: re.Match) -> str:
        alvo = encontrado.group(1)
        if "://" in alvo or alvo.startswith(("#", "mailto:")):
            return encontrado.group(0)
        caminho = posixpath.normpath(posixpath.join(posixpath.dirname(origem), alvo))
        return f"]({REPOSITORIO}/blob/main/{caminho})"

    return _LINK.sub(trocar, texto)


def _para_html(texto: str, origem: str) -> str:
    return markdown.markdown(_links_para_o_github(texto, origem), extensions=["tables"])


SAIDA = {"v1": "entregas/v1/relatorio.pdf", "v2": "relatorio.pdf"}
SECAO_DO_MEMO = {"v1": "d", "v2": "e"}


def _html(versao: str) -> str:
    origem_relatorio, origem_memo = (
        f"docs/{versao}/relatorio.md",
        f"docs/{versao}/memo-professor.md",
    )
    secao = SECAO_DO_MEMO[versao]
    relatorio = (RAIZ / origem_relatorio).read_text()
    # A última seção é o próprio memo, na última página, em vez do link para ele.
    relatorio = re.sub(rf"## {secao}\) Memo ao professor\s+Em \[[^\n]*\n?", "", relatorio)
    memo = (RAIZ / origem_memo).read_text()
    memo = memo.replace("# Memo ao professor", f"## {secao}) Memo ao professor", 1)
    partes = [
        _para_html(relatorio, origem_relatorio),
        f'<div class="memo">{_para_html(memo, origem_memo)}</div>',
    ]
    titulo = "<title>Relatório — classificação de tópicos</title>"
    cabecalho = f'<!doctype html><meta charset="utf-8">{titulo}'
    return f"{cabecalho}<style>{ESTILO}</style>{''.join(partes)}"


def _chrome(argumento: str | None) -> str:
    candidatos = [argumento, os.environ.get("CHROME")]
    candidatos += [shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome")]
    encontrado = next((c for c in candidatos if c), None)
    if encontrado is None:
        raise SystemExit("Chrome/Chromium não encontrado: passe o caminho ou defina CHROME")
    return encontrado


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in SAIDA:
        raise SystemExit("uso: gerar_relatorio_pdf.py {v1,v2} [chrome]")
    versao = sys.argv[1]
    chrome = _chrome(sys.argv[2] if len(sys.argv) > 2 else None)
    saida = RAIZ / SAIDA[versao]
    with tempfile.TemporaryDirectory() as pasta:
        pagina = Path(pasta) / "relatorio.html"
        pagina.write_text(_html(versao))
        subprocess.run(
            [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={saida}", pagina.as_uri()],
            check=True, capture_output=True,
        )  # fmt: skip
    print(f"{saida.relative_to(RAIZ)}: {_paginas(saida)} páginas")


def _paginas(pdf: Path) -> int:
    dados = pdf.read_bytes()
    return dados.count(b"/Type /Page") - dados.count(b"/Type /Pages")


if __name__ == "__main__":
    main()
