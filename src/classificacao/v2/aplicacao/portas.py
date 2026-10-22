from typing import Protocol


class FalhaDoModelo(Exception):
    pass


class ModeloDeLinguagem(Protocol):
    """Usado só antes da decisão (ex.: enriquecer temas); nunca vê uma Questão avaliada."""

    identificador: str

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict: ...
