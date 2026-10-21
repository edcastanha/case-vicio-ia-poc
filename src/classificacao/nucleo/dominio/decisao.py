from dataclasses import dataclass
from enum import Enum


class Decisao(Enum):
    PUBLICAR = "publicar"
    REVISAR = "revisar"
    FORA = "fora"


@dataclass(frozen=True)
class Resultado:
    decisao: Decisao
    tema_central_id: int | None
    motivo: str = ""
