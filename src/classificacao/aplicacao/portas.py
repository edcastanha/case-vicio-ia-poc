from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from classificacao.aplicacao.classificar_questao import Classificacao


class FalhaDoModelo(Exception):
    """O provedor não respondeu, ou respondeu algo que não dá para usar."""


class ModeloDeLinguagem(Protocol):
    identificador: str

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict: ...


class FilaDeFalhas(Protocol):
    def registrar(self, questao_id: str, papel: str, erro: str) -> None: ...


class Cache(Protocol):
    def obter(self, chave: str) -> dict | None: ...

    def guardar(self, chave: str, valor: dict) -> None: ...


class RegistroDeClassificacoes(Protocol):
    def ja_classificada(self, questao_id: str) -> bool: ...

    def salvar(self, classificacao: "Classificacao") -> None: ...
