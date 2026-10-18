import csv
from collections.abc import Sequence
from pathlib import Path

from classificacao.aplicacao.amostra_cega import ItemDeRotulagem
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


def _rotulo(questao_id: str, resposta: str, arvore: Arvore) -> int | None:
    if resposta.casefold() == _NENHUM:
        return None
    # Aceita um candidato colado como está na planilha ("id — caminho"), se o caminho bater.
    no, _, caminho = (parte.strip() for parte in resposta.partition("—"))
    if no.isdigit() and arvore.pode_receber_questao(int(no)):
        if caminho and " ".join(caminho.split()) != arvore.no(int(no)).caminho:
            raise RotuloInvalido(
                f"{questao_id}: o caminho de {resposta!r} não é o do nó {no} "
                f"({arvore.no(int(no)).caminho})"
            )
        return int(no)
    raise RotuloInvalido(
        f"{questao_id}: resposta {resposta!r} não é um Tema/Subtema ativo nem 'nenhum'"
    )
