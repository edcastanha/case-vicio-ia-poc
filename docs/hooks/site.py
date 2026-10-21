"""Hook do MkDocs: lê os arquivos do repositório e gera as páginas que não existem em docs/.

A lógica fica em classificacao.v1.entrada.site (testada sem I/O); aqui só há leitura de arquivos.
"""

import csv
from pathlib import Path

from mkdocs.structure.files import File

from classificacao.nucleo.adaptadores.anexos import ler_arvore, ler_questoes
from classificacao.v1.adaptadores.arquivos import RegistroEmArquivo
from classificacao.v1.adaptadores.rotulagem import ler_rotulos
from classificacao.v1.entrada.site import bloco_da_previsao, corrigir_links, pagina_de_resultados

RAIZ = Path(__file__).resolve().parents[2]
FONTE_DOS_ROTULOS = "agente jurídico"  # ADR 0006
REPOSITORIO = "https://github.com/edcastanha/case-vicio-ia-poc"
# Arquivo do repositório → página do site; os textos continuam com um dono só (o arquivo).
PAGINAS_DA_RAIZ = {
    "README.md": "como-rodar.md",
    "GLOSSARY.md": "glossario.md",
    "dados/v1/README.md": "dados.md",
}


def on_files(files, config):
    for origem, pagina in PAGINAS_DA_RAIZ.items():
        texto = corrigir_links((RAIZ / origem).read_text(), origem, PAGINAS_DA_RAIZ, REPOSITORIO)
        files.append(File.generated(config, pagina, content=texto))
    files.append(File.generated(config, "resultados.md", content=_resultados()))
    return files


def on_page_markdown(markdown, page, config, files):
    if page.file.src_uri != "index.md":
        return markdown
    previsao = RAIZ / "entregas/v1/previsao.txt"
    bloco = bloco_da_previsao(previsao.read_text() if previsao.exists() else None)
    return markdown.replace("<!-- previsao -->", bloco)


def _resultados() -> str:
    zip_anexos = RAIZ / "anexos/v1/anexos-case-ia.zip"
    classificacoes = RegistroEmArquivo(RAIZ / "dados/v1/rodada/classificacoes.jsonl").todas()
    return pagina_de_resultados(
        {c.questao_id: c for c in classificacoes},
        {q.id: q for q in ler_questoes(zip_anexos)},
        ler_arvore(zip_anexos),
        _entrega(RAIZ / "entregas/v1/publicacao.csv"),
        _amostra(RAIZ / "dados/v1/rotulagem.csv", ler_arvore(zip_anexos)),
    )


def _entrega(caminho: Path) -> dict[str, dict[str, str]] | None:
    if not caminho.exists():
        return None
    with caminho.open(newline="") as arquivo:
        return {linha["id"]: linha for linha in csv.DictReader(arquivo)}


def _amostra(caminho: Path, arvore) -> dict[str, tuple[int | None, str]]:
    if not caminho.exists():
        return {}
    return {id: (no_id, FONTE_DOS_ROTULOS) for id, no_id in ler_rotulos(caminho, arvore).items()}
