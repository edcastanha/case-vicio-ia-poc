import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

from classificacao.aplicacao.amostra_cega import ItemDeRotulagem
from classificacao.aplicacao.rotulagem_assistida import ItemDeArbitragem
from classificacao.dominio.arvore import Arvore

_NENHUM = "nenhum"


class RotuloInvalido(ValueError):
    pass


def escrever_planilha(itens: Sequence[ItemDeRotulagem], arvore: Arvore, caminho: Path) -> None:
    """Planilha cega: a questão e os candidatos embaralhados, sem Origem nem votos."""
    maximo = max(len(item.candidatos) for item in itens)
    colunas = ["id", "enunciado", "comando", "alternativas"]
    colunas += [f"candidato_{i}" for i in range(1, maximo + 1)]
    colunas += ["resposta", "observacao"]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for item in itens:
            q = item.questao
            linha = {
                "id": q.id,
                "enunciado": q.enunciado,
                "comando": q.comando,
                "alternativas": "\n".join(
                    f"{letra}) {texto}" for letra, texto in q.alternativas.items()
                ),
                "resposta": "",
                "observacao": "",
            }
            for i, no_id in enumerate(item.candidatos, start=1):
                linha[f"candidato_{i}"] = f"{no_id} — {arvore.no(no_id).caminho}"
            escritor.writerow(linha)


def ler_rotulos(caminho: Path, arvore: Arvore) -> dict[str, int | None]:
    """Rótulo de cada Questão já rotulada: o nó certo, ou None quando nenhum nó serve."""
    rotulos: dict[str, int | None] = {}
    with caminho.open(newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            resposta = (linha.get("resposta") or "").strip()
            if not resposta:
                continue
            rotulos[linha["id"]] = _rotulo(linha["id"], resposta, arvore)
    return rotulos


def ids_da_planilha(caminho: Path) -> list[str]:
    with caminho.open(newline="") as arquivo:
        return [linha["id"] for linha in csv.DictReader(arquivo)]


def preencher_respostas(caminho: Path, respostas: Mapping[str, tuple[int | None, str]]) -> None:
    """Grava resposta e quem a deu; resposta que um humano já preencheu nunca é trocada."""
    with caminho.open(newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        colunas, linhas = list(leitor.fieldnames or []), list(leitor)
    for linha in linhas:
        if linha["id"] in respostas and not (linha.get("resposta") or "").strip():
            no_id, fonte = respostas[linha["id"]]
            linha["resposta"] = _NENHUM if no_id is None else str(no_id)
            linha["observacao"] = fonte
    with caminho.open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def escrever_planilha_de_arbitragem(
    itens: Sequence[ItemDeArbitragem], arvore: Arvore, caminho: Path
) -> None:
    """Conflitos com as opções A e B, sem dizer qual veio do Rotulador e qual do pipeline."""
    colunas = ["id", "enunciado", "comando", "alternativas", "opcao_a", "opcao_b"]
    colunas += ["escolha", "observacao"]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for item in itens:
            q = item.questao
            linha = {
                "id": q.id,
                "enunciado": q.enunciado,
                "comando": q.comando,
                "alternativas": "\n".join(
                    f"{letra}) {texto}" for letra, texto in q.alternativas.items()
                ),
                "opcao_a": "",
                "opcao_b": "",
                "escolha": "",
                "observacao": "",
            }
            for coluna, no_id in zip(("opcao_a", "opcao_b"), item.opcoes, strict=False):
                linha[coluna] = _opcao(no_id, arvore)
            escritor.writerow(linha)


def ler_escolhas(caminho: Path, arvore: Arvore) -> dict[str, int | None]:
    """Escolha de cada Conflito já arbitrado: A, B, outro Nó ou 'nenhum'."""
    escolhas: dict[str, int | None] = {}
    with caminho.open(newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            escolha = (linha.get("escolha") or "").strip()
            if not escolha:
                continue
            coluna = {"a": "opcao_a", "b": "opcao_b"}.get(escolha.casefold())
            if coluna is not None:
                opcao = (linha.get(coluna) or "").strip()
                if not opcao:
                    raise RotuloInvalido(f"{linha['id']}: escolha {escolha!r} sem opção")
                escolha = opcao.split(" — ", 1)[0]
            escolhas[linha["id"]] = _rotulo(linha["id"], escolha, arvore)
    return escolhas


def _opcao(no_id: int | None, arvore: Arvore) -> str:
    if no_id is None:
        return f"{_NENHUM} — nenhum nó da árvore serve"
    return f"{no_id} — {arvore.no(no_id).caminho}"


def _rotulo(questao_id: str, resposta: str, arvore: Arvore) -> int | None:
    if resposta.casefold() == _NENHUM:
        return None
    if resposta.isdigit() and arvore.pode_receber_questao(int(resposta)):
        return int(resposta)
    raise RotuloInvalido(
        f"{questao_id}: resposta {resposta!r} não é um Tema/Subtema ativo nem 'nenhum'"
    )
