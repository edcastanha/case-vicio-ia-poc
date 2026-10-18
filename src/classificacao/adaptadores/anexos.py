import csv
import io
import json
import re
import unicodedata
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from classificacao.dominio.arvore import Arvore, No
from classificacao.dominio.questao import Questao

_ESPACOS = re.compile(r"[ \t\u00a0]+")
_QUEBRAS = {"br", "p"}
# Conteúdo que o navegador não mostra ao aluno; nunca vai ao modelo (ADR 0005).
_ELEMENTOS_INVISIVEIS = {"head", "noscript", "script", "style", "template", "title", "xml"}
_ESTILO_INVISIVEL = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden"
    r"|(font-size|opacity)\s*:\s*0+(\.0+)?(px|pt|em|rem|%)?\s*(;|!|$)",
    re.IGNORECASE,
)
_VAZIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "wbr"}


class _TextoVisivel(HTMLParser):
    """Só o texto que aparece na tela; comentários (inclusive os condicionais do Word) somem."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._escondido: str | None = None  # tag que abriu o trecho invisível
        self._profundidade = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._escondido is not None:
            self._profundidade += tag == self._escondido
            return
        atributos = dict(attrs)
        invisivel = (
            tag in _ELEMENTOS_INVISIVEIS
            or "hidden" in atributos
            or bool(_ESTILO_INVISIVEL.search(atributos.get("style") or ""))
        )
        if invisivel and tag not in _VAZIOS:
            self._escondido, self._profundidade = tag, 1
        elif tag in _QUEBRAS:
            self.partes.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._escondido is not None:
            self._profundidade -= tag == self._escondido
            if self._profundidade == 0:
                self._escondido = None
        elif tag == "p":
            self.partes.append("\n")

    def handle_data(self, data: str) -> None:
        if self._escondido is None:
            self.partes.append(data.replace("\r", " ").replace("\n", " "))


def limpar_html(texto_html: str) -> str:
    """Texto como o aluno lê: quebras de linha do <br>, sem tags, entidades nem invisíveis."""
    leitor = _TextoVisivel()
    leitor.feed(texto_html)
    leitor.close()
    texto = "".join(c for c in "".join(leitor.partes) if c == "\n" or not _invisivel(c))
    linhas = (_ESPACOS.sub(" ", linha).strip() for linha in texto.split("\n"))
    return "\n".join(linha for linha in linhas if linha)


def _invisivel(caractere: str) -> bool:
    """Controle e formatação (largura zero, bidi, hífen invisível, tags Unicode)."""
    return unicodedata.category(caractere) in {"Cc", "Cf"}


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
