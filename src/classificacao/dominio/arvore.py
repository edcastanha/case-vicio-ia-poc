from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class No:
    id: int
    pai_id: int | None
    nivel: int
    caminho: str
    ativo: bool = True


class Arvore:
    def __init__(self, nos: Iterable[No]) -> None:
        self._nos = {no.id: no for no in nos}

    def mesmo_ramo(self, a: int, b: int) -> bool:
        if a not in self._nos or b not in self._nos:
            return False
        return a == b or self._nos[a].pai_id == b or self._nos[b].pai_id == a

    def pode_receber_questao(self, id: int) -> bool:
        no = self._nos.get(id)
        return no is not None and no.ativo and no.nivel > 0

    def no_de_consenso(self, a: int, b: int) -> int | None:
        if a not in self._nos or b not in self._nos:
            return None
        if a == b:
            candidato = a
        elif self._nos[a].pai_id == b:
            candidato = b
        elif self._nos[b].pai_id == a:
            candidato = a
        elif self._nos[a].pai_id == self._nos[b].pai_id:
            candidato = self._nos[a].pai_id
        else:
            return None
        return candidato if self.pode_receber_questao(candidato) else None

    def nos_que_podem_receber_questao(self) -> list[No]:
        return [no for no in self._nos.values() if self.pode_receber_questao(no.id)]

    def no(self, id: int) -> No | None:
        return self._nos.get(id)
