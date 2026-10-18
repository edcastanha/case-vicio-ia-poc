"""Páginas geradas do site MkDocs: resultados da rodada, previsão e links dos .md da raiz.

Sem I/O: o hook em docs/hooks/site.py lê os arquivos e passa os dados para cá.
"""

import html
import posixpath
import re
from collections import Counter
from collections.abc import Mapping

from classificacao.aplicacao.classificar_questao import Classificacao, Proposta, situacao
from classificacao.aplicacao.rotulagem_assistida import no_do_pipeline
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.questao import Questao

_LINK = re.compile(r"\]\(([^)\s]+)\)")
_AVISO_SEM_ENTREGA = (
    '!!! note "Resultado final: entrega ainda não gerada"\n'
    "    Os números abaixo são da rodada de classificação. Decisão, confiança e previsão "
    "aparecem quando `classificacao entrega` gerar `publicacao.csv` e `previsao.txt`.\n"
)
_ROTULOS_DA_PREVISAO = {
    "precisao": "Precisão nas publicadas",
    "cobertura": "Cobertura (fração publicada)",
}


def corrigir_links(markdown: str, origem: str, paginas: Mapping[str, str], repositorio: str) -> str:
    """Links de um .md do repositório reescritos para o site.

    `origem` é o caminho do arquivo no repositório e `paginas` mapeia arquivo do repositório
    para página do site. O que está em docs/ vira página; o resto aponta para o GitHub.
    """

    def trocar(encontrado: re.Match) -> str:
        alvo = encontrado.group(1)
        if "://" in alvo or alvo.startswith(("#", "mailto:")):
            return encontrado.group(0)
        caminho = posixpath.normpath(posixpath.join(posixpath.dirname(origem), alvo))
        caminho += "/" if alvo.endswith("/") else ""
        if caminho in paginas:
            return f"]({paginas[caminho]})"
        if caminho.startswith("docs/") and caminho.endswith(".md"):
            return f"]({caminho.removeprefix('docs/')})"
        tipo = "tree" if caminho.endswith("/") else "blob"
        return f"]({repositorio}/{tipo}/main/{caminho})"

    return _LINK.sub(trocar, markdown)


def bloco_da_previsao(previsao: str | None) -> str:
    if previsao is None:
        return _AVISO_SEM_ENTREGA
    # As 4 primeiras linhas são os valores do LEIA-ME; depois vem a explicação em texto livre.
    valores_e_explicacao = previsao.splitlines()
    valores = dict(linha.split(":", 1) for linha in valores_e_explicacao[:4])
    linhas = ["| | Previsto | Intervalo |", "|---|---|---|"]
    for chave, rotulo in _ROTULOS_DA_PREVISAO.items():
        ponto = _porcento(valores[f"{chave}_prevista"])
        minimo, maximo = (_porcento(v) for v in valores[f"{chave}_intervalo"].split("-"))
        linhas.append(f"| {rotulo} | {ponto} | {minimo} – {maximo} |")
    explicacao = "\n".join(valores_e_explicacao[4:]).strip()
    return "\n".join(linhas) + "\n" + (f"\n{explicacao}\n" if explicacao else "")


def pagina_de_resultados(
    classificacoes: Mapping[str, Classificacao],
    questoes: Mapping[str, Questao],
    arvore: Arvore,
    entrega: Mapping[str, Mapping[str, str]] | None,
    amostra: Mapping[str, tuple[int | None, str]],
) -> str:
    """Contagens, tabela filtrável das Questões e o detalhe de cada uma, recolhido."""
    ids = sorted(questoes)
    situacoes = {id: _situacao(classificacoes.get(id), arvore) for id in ids}
    partes = ["# Resultados", ""]
    partes += [_AVISO_SEM_ENTREGA] if entrega is None else []
    partes += ["## Rodada de classificação", "", _contagem("Situação", situacoes.values())]
    if entrega is not None:
        decisoes = (entrega.get(id, {}).get("decisao", "—") for id in ids)
        partes += ["## Decisões da entrega", "", _contagem("Decisão", decisoes)]
    partes += [
        "## Questões",
        "",
        "Clique no id para ver o enunciado e o voto de cada papel. "
        "Clique no cabeçalho de uma coluna para ordenar.",
        "",
        '<input id="filtro-questoes" type="search" placeholder="Filtrar (ex.: desacordo, '
        'publicar, Júri)" aria-label="Filtrar questões">',
        "",
        "| Questão | Situação | Nó do pipeline | Decisão | Confiança | Amostra |",
        "|---|---|---|---|---|---|",
    ]
    for id in ids:
        c = classificacoes.get(id)
        linha_da_entrega = (entrega or {}).get(id, {})
        celulas = [
            f"[{id}](#{id.lower()})",
            situacoes[id],
            _no(no_do_pipeline(c, arvore), arvore),
            linha_da_entrega.get("decisao", "—"),
            linha_da_entrega.get("confianca", "—"),
            _amostra(amostra.get(id)),
        ]
        partes.append("| " + " | ".join(_celula(celula) for celula in celulas) + " |")
    partes += ["", "## Detalhe por Questão", ""]
    partes += [_detalhe(questoes[id], classificacoes.get(id), situacoes[id], arvore) for id in ids]
    return "\n".join(partes) + "\n"


def _situacao(classificacao: Classificacao | None, arvore: Arvore) -> str:
    if classificacao is None:
        return "não classificada"
    return situacao(classificacao, arvore).replace("mesmo no", "mesmo nó")


def _contagem(titulo: str, valores) -> str:
    linhas = [f"| {titulo} | Questões |", "|---|---|"]
    linhas += [f"| {valor} | {n} |" for valor, n in Counter(valores).most_common()]
    return "\n".join(linhas) + "\n"


def _no(no_id: int | None, arvore: Arvore) -> str:
    if no_id is None:
        return "nenhum"
    no = arvore.no(no_id)
    return f"{no_id} — {no.caminho}" if no else f"{no_id} (inexistente)"


def _amostra(resposta: tuple[int | None, str] | None) -> str:
    if resposta is None:
        return "—"
    no_id, fonte = resposta
    return f"{'nenhum' if no_id is None else no_id} ({fonte})"


def _celula(texto: str) -> str:
    return texto.replace("|", "\\|")


def _detalhe(
    questao: Questao, classificacao: Classificacao | None, situacao: str, arvore: Arvore
) -> str:
    e = html.escape
    alternativas = "".join(
        f"<li>{e(letra)}) {e(texto)}</li>" for letra, texto in questao.alternativas.items()
    )
    votos = "".join(
        _linha_do_voto(papel, proposta, arvore)
        for papel, proposta in (
            ("Classificador", classificacao and classificacao.classificador),
            ("Verificador", classificacao and classificacao.verificador),
            ("Desempatador", classificacao and classificacao.desempatador),
        )
        if proposta is not None
    )
    return "\n".join(
        [
            f'<details id="{questao.id.lower()}">',
            f"<summary><strong>{e(questao.id)}</strong> — {e(situacao)}</summary>",
            f"<p>{e(questao.enunciado).replace(chr(10), '<br>')}</p>",
            f"<p><em>{e(questao.comando)}</em></p>" if questao.comando else "",
            f"<ul>{alternativas}</ul>",
            f"<p>Origem (site de onde veio): {e(questao.disciplina_origem)} &gt; "
            f"{e(questao.assunto_origem)}</p>",
            "<table><thead><tr><th>Papel</th><th>Nó</th><th>Confiança</th>"
            f"<th>Justificativa</th><th>Prompt</th></tr></thead><tbody>{votos}</tbody></table>",
            "</details>",
            "",
        ]
    )


def _linha_do_voto(papel: str, proposta: Proposta, arvore: Arvore) -> str:
    e = html.escape
    return (
        f"<tr><td>{papel}</td><td>{e(_no(proposta.no_id, arvore))}</td>"
        f"<td>{proposta.confianca:.2f}</td><td>{e(proposta.justificativa)}</td>"
        f"<td><code>{e(proposta.prompt or '—')}</code></td></tr>"
    )


def _porcento(valor: str) -> str:
    return f"{float(valor.strip()):.0%}"
