import json
import subprocess
from collections.abc import Callable

from classificacao.v2.aplicacao.portas import FalhaDoModelo

_TEMPO_LIMITE_EM_SEGUNDOS = 900


class ModeloClaudeCode:
    """`claude -p` da assinatura do usuário, sem ferramentas e com saída presa a um schema."""

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
                comando, input=usuario, capture_output=True, text=True,
                timeout=_TEMPO_LIMITE_EM_SEGUNDOS,
            )  # fmt: skip
        except subprocess.TimeoutExpired as erro:
            raise FalhaDoModelo(f"claude -p excedeu {_TEMPO_LIMITE_EM_SEGUNDOS}s") from erro
        try:
            envelope = json.loads(processo.stdout)
        except json.JSONDecodeError as erro:
            raise FalhaDoModelo(f"claude -p sem JSON (código {processo.returncode})") from erro
        resposta = envelope.get("structured_output") if isinstance(envelope, dict) else None
        if processo.returncode != 0 or envelope.get("is_error") or not isinstance(resposta, dict):
            raise FalhaDoModelo(f"claude -p falhou: {envelope.get('result')!r}")
        return resposta
