import csv
import html
import io
import json
import re
import zipfile
from pathlib import Path

from classificacao.dominio.arvore import Arvore, No
from classificacao.dominio.questao import Questao

_QUEBRA = re.compile(r"<\s*br\s*/?\s*>|<\s*/?\s*p\b[^>]*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_ESPACOS = re.compile(r"[ \t ]+")


def limpar_html(texto_html: str) -> str:
    """Texto como o aluno lê: quebras de linha do <br>, sem tags nem entidades."""
    texto = texto_html.replace("\r", " ").replace("\n", " ")
    texto = _QUEBRA.sub("\n", texto)
    texto = html.unescape(_TAG.sub("", texto))
    linhas = (_ESPACOS.sub(" ", linha).strip() for linha in texto.split("\n"))
    return "\n".join(linha for linha in linhas if linha)


def ler_questoes(zip_anexos: Path) -> list[Questao]:
    linhas = _ler_texto(zip_anexos, "questoes.jsonl").splitlines()
    return [_questao(json.loads(linha)) for linha in linhas if linha.strip()]


def _questao(bruta: dict) -> Questao:
    return Questao(
        id=bruta["id"],
        enunciado=limpar_html(bruta["enunciado_html"]),
        comando=limpar_html(bruta["comando"]),
        alternativas={letra: limpar_html(texto) for letra, texto in bruta["alternativas"].items()},
        disciplina_origem=bruta["disciplina_origem"].strip(),
        assunto_origem=bruta["assunto_origem"].strip(),
    )


def _ler_texto(zip_anexos: Path, nome: str) -> str:
    with zipfile.ZipFile(zip_anexos) as arquivo:
        [caminho] = [n for n in arquivo.namelist() if n.rsplit("/", 1)[-1] == nome]
        return arquivo.read(caminho).decode("utf-8")


def ler_arvore(zip_anexos: Path) -> Arvore:
    linhas = csv.DictReader(io.StringIO(_ler_texto(zip_anexos, "temas.csv")))
    return Arvore(
        No(
            id=int(linha["tema_id"]),
            pai_id=int(linha["parent_id"]) if linha["parent_id"] else None,
            nivel=int(linha["nivel"]),
            caminho=linha["caminho"].strip(),
            ativo=linha["status"].strip() == "active",
        )
        for linha in linhas
    )
