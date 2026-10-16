import json
import subprocess
from collections.abc import Callable

from classificacao.aplicacao.portas import FalhaDoModelo

_TEMPO_LIMITE_EM_SEGUNDOS = 600


class ModeloClaudeCode:
    """Backend de teste: usa o `claude -p` da assinatura do usuário, sem chave de API."""

    def __init__(
        self, modelo: str, executar: Callable[..., subprocess.CompletedProcess] = subprocess.run
    ):
        self.modelo = modelo
        self.identificador = f"claude-code:{modelo}"
        self._executar = executar

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict:
        comando = [
            "claude",
            "-p",
            "--model",
            self.modelo,
            "--output-format",
            "json",
            "--no-session-persistence",
            "--tools",
            "",
            "--json-schema",
            json.dumps(schema),
            "--system-prompt",
            sistema,
        ]
        try:
            processo = self._executar(
                comando,
                input=usuario,
                capture_output=True,
                text=True,
                timeout=_TEMPO_LIMITE_EM_SEGUNDOS,
            )
        except subprocess.TimeoutExpired as erro:
            raise FalhaDoModelo(f"claude -p excedeu {_TEMPO_LIMITE_EM_SEGUNDOS}s") from erro
        if processo.returncode != 0:
            raise FalhaDoModelo(
                f"claude -p saiu com código {processo.returncode}: {processo.stderr}"
            )
        return _voto_do_envelope(processo.stdout)


def _voto_do_envelope(saida: str) -> dict:
    try:
        envelope = json.loads(saida)
    except json.JSONDecodeError as erro:
        raise FalhaDoModelo("claude -p não devolveu JSON") from erro
    if envelope.get("is_error") or envelope.get("subtype") != "success":
        raise FalhaDoModelo(f"claude -p devolveu erro: {envelope.get('result')!r}")
    voto = envelope.get("structured_output")
    if not isinstance(voto, dict):
        raise FalhaDoModelo("envelope do claude -p sem structured_output")
    return voto
