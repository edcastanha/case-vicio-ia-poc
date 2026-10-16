from dataclasses import dataclass


@dataclass(frozen=True)
class Questao:
    id: str
    enunciado: str
    comando: str
    alternativas: dict[str, str]
    disciplina_origem: str
    assunto_origem: str
