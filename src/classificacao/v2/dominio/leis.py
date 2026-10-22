"""Leis citadas no texto de uma Questão, pelo número ou pelo apelido do dicionário de leis."""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Lei:
    numero: str  # sem pontos: "11340"
    nome: str
    apelidos: tuple[str, ...]  # minúsculas e sem acento, como saem de normalizar()
    nos: tuple[int, ...]  # Nós da Árvore de temas que tratam da lei; vazio nos códigos gerais


_NUMERO = re.compile(
    r"\b(?:lei|decreto-lei|lei complementar)\s+(?:federal\s+)?(?:n[o.]?\s*)?(\d{1,2}\.?\d{3})\b"
)


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e com "nº"/"n°" virando "no", para casar grafias diferentes."""
    sem_ordinal = texto.replace("º", "o").replace("°", "o")
    decomposto = unicodedata.normalize("NFKD", sem_ordinal.casefold())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def leis_citadas(texto: str, leis: Sequence[Lei]) -> tuple[str, ...]:
    """Números das leis citadas, ordenados; inclui leis numeradas que o dicionário não tem."""
    normal = normalizar(texto)
    numeros = {m.group(1).replace(".", "") for m in _NUMERO.finditer(normal)}
    numeros |= {
        lei.numero
        for lei in leis
        if any(re.search(rf"\b{re.escape(apelido)}\b", normal) for apelido in lei.apelidos)
    }
    return tuple(sorted(numeros))
