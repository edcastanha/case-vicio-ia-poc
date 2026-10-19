import json
import threading
from dataclasses import asdict
from pathlib import Path

from classificacao.aplicacao.classificar_questao import Classificacao, Proposta


class CacheEmDisco:
    """Um arquivo JSON por chave; apagar a pasta zera o cache."""

    def __init__(self, pasta: Path) -> None:
        self._pasta = pasta
        self._pasta.mkdir(parents=True, exist_ok=True)

    def obter(self, chave: str) -> dict | None:
        arquivo = self._pasta / f"{chave}.json"
        return json.loads(arquivo.read_text()) if arquivo.exists() else None

    def guardar(self, chave: str, valor: dict) -> None:
        (self._pasta / f"{chave}.json").write_text(json.dumps(valor, ensure_ascii=False))


class FilaDeFalhasEmArquivo:
    """DLQ: uma falha por linha, só acrescentando."""

    def __init__(self, caminho: Path) -> None:
        self._trava = threading.Lock()
        self._caminho = caminho
        self._caminho.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, questao_id: str, papel: str, erro: str) -> None:
        linha = {"questao_id": questao_id, "papel": papel, "erro": erro}
        with self._trava, self._caminho.open("a") as arquivo:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")


class RegistroEmArquivo:
    """Uma Classificacao por linha; reabrir o arquivo retoma de onde parou."""

    def __init__(self, caminho: Path) -> None:
        self._caminho = caminho
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        self._classificacoes = {c.questao_id: c for c in self._ler()}

    def ja_classificada(self, questao_id: str) -> bool:
        classificacao = self._classificacoes.get(questao_id)
        return classificacao is not None and classificacao.completa

    def salvar(self, classificacao: Classificacao) -> None:
        with self._caminho.open("a") as arquivo:
            arquivo.write(json.dumps(asdict(classificacao), ensure_ascii=False) + "\n")
        self._classificacoes[classificacao.questao_id] = classificacao

    def todas(self) -> list[Classificacao]:
        return list(self._classificacoes.values())

    def _ler(self) -> list[Classificacao]:
        if not self._caminho.exists():
            return []
        return [
            _classificacao(json.loads(linha)) for linha in self._caminho.read_text().splitlines()
        ]


def gravar_propostas(caminho: Path, propostas: dict[str, Proposta]) -> None:
    """Uma Proposta por Questão, num JSON legível (ex.: os rótulos do Rotulador)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = {id: asdict(proposta) for id, proposta in sorted(propostas.items())}
    caminho.write_text(json.dumps(conteudo, ensure_ascii=False, indent=1) + "\n")


def ler_propostas(caminho: Path) -> dict[str, Proposta]:
    return {id: _proposta(bruta) for id, bruta in json.loads(caminho.read_text()).items()}


def _classificacao(bruta: dict) -> Classificacao:
    return Classificacao(
        bruta["questao_id"],
        *(
            None if bruta[papel] is None else _proposta(bruta[papel])
            for papel in ("classificador", "verificador", "desempatador")
        ),
        tuple(bruta.get("indicios_de_injecao", ())),
    )


def _proposta(bruta: dict) -> Proposta:
    return Proposta(
        bruta["no_id"],
        bruta["confianca"],
        bruta["justificativa"],
        tuple(bruta["extras"]),
        bruta.get("prompt", ""),  # linhas de antes do versionamento não têm o campo
    )
