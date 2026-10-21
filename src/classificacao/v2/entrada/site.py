"""Página de resultados da v2 no site MkDocs; sem I/O (o hook lê os arquivos)."""

from collections import Counter
from collections.abc import Mapping, Sequence

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.regua import Gabarito, certo_pela_regua


def pagina_de_resultados(
    linhas: Sequence[Mapping[str, str]], arvore: Arvore, folha: Mapping[str, Gabarito]
) -> str:
    decisoes = Counter(linha["decisao"] for linha in linhas)
    partes = [
        "# Resultados da v2\n",
        "Cada uma das Questões do `publicacao.csv`, com a decisão do Ranqueador, a confiança "
        "calibrada e o motivo. Nas 100 da Folha-verdade, a coluna *Folha-verdade* diz se o Tema "
        "está certo pela Régua; elas não entram na avaliação da Vício.\n",
        "| Decisão | Questões |",
        "|---|---|",
        *(f"| {d} | {decisoes[d]} |" for d in ("publicar", "revisar", "fora")),
        "",
        "| Questão | Decisão | Tema central | Confiança | Motivo | Folha-verdade |",
        "|---|---|---|---|---|---|",
    ]
    for linha in linhas:
        tema = int(linha["tema_central_id"]) if linha["tema_central_id"] else None
        caminho = arvore.no(tema).caminho if tema is not None else "—"
        partes.append(
            f"| {linha['id']} | {linha['decisao']} | {_celula(caminho)} | {linha['confianca']} "
            f"| {_celula(linha['motivo'])} | {_na_folha(linha['id'], tema, arvore, folha)} |"
        )
    return "\n".join(partes) + "\n"


def _na_folha(questao_id: str, tema: int | None, arvore: Arvore, folha) -> str:
    if questao_id not in folha:
        return ""
    gabarito = folha[questao_id]
    if tema is None:
        return "certo" if gabarito.fora else "errado"
    return "certo" if certo_pela_regua(arvore, tema, gabarito) else "errado"


def _celula(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " ")
