from collections.abc import Callable

from classificacao.aplicacao.portas import FalhaDoModelo


class ModeloFake:
    """Responde com uma função das mensagens e guarda cada chamada recebida."""

    def __init__(self, identificador: str, responder: Callable[[str, str], dict]) -> None:
        self.identificador = identificador
        self._responder = responder
        self.chamadas: list[tuple[str, str]] = []

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict:
        self.chamadas.append((sistema, usuario))
        return self._responder(sistema, usuario)


def sempre(no_id: int | None, confianca: float = 0.9) -> Callable[[str, str], dict]:
    return lambda sistema, usuario: {
        "no_id": no_id,
        "confianca": confianca,
        "justificativa": f"escolhi {no_id}",
        "extras": [],
    }


def falha_sempre(sistema: str, usuario: str) -> dict:
    raise FalhaDoModelo("provedor fora do ar")


class FilaDeFalhasEmMemoria:
    def __init__(self) -> None:
        self.falhas: list[tuple[str, str, str]] = []

    def registrar(self, questao_id: str, papel: str, erro: str) -> None:
        self.falhas.append((questao_id, papel, erro))


class CacheEmMemoria:
    def __init__(self) -> None:
        self.valores: dict[str, dict] = {}

    def obter(self, chave: str) -> dict | None:
        return self.valores.get(chave)

    def guardar(self, chave: str, valor: dict) -> None:
        self.valores[chave] = valor


def em_sequencia(*respostas: Callable[[str, str], dict]) -> Callable[[str, str], dict]:
    """Cada chamada usa a próxima resposta; a última se repete."""
    fila = list(respostas)

    def responder(sistema: str, usuario: str) -> dict:
        atual = fila.pop(0) if len(fila) > 1 else fila[0]
        return atual(sistema, usuario)

    return responder


def malformada(sistema: str, usuario: str) -> dict:
    return {"confianca": 0.9}


class RegistroEmMemoria:
    def __init__(self) -> None:
        self.classificacoes: dict[str, object] = {}

    def ja_classificada(self, questao_id: str) -> bool:
        return questao_id in self.classificacoes

    def salvar(self, classificacao) -> None:
        self.classificacoes[classificacao.questao_id] = classificacao
