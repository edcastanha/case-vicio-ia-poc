import json

import anthropic

from classificacao.aplicacao.portas import FalhaDoModelo

_FALLBACK_DE_RECUSA = "server-side-fallback-2026-07-01"


class ModeloAnthropic:
    """Classificador no backend api: Messages API com saída JSON imposta pelo schema."""

    def __init__(
        self,
        modelo: str,
        cliente: anthropic.Anthropic | None = None,
        esforco: str = "high",
        max_tokens: int = 16000,
    ) -> None:
        self.modelo = modelo
        self.identificador = f"api:{modelo}"
        self._cliente = cliente or anthropic.Anthropic()
        self._esforco = esforco
        self._max_tokens = max_tokens

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict:
        try:
            resposta = self._cliente.beta.messages.create(
                model=self.modelo,
                max_tokens=self._max_tokens,
                # Instruções + árvore são iguais em toda chamada: cache de 1h no prefixo.
                system=[
                    {
                        "type": "text",
                        "text": sistema,
                        "cache_control": {"type": "ephemeral", "ttl": "1h"},
                    }
                ],
                messages=[{"role": "user", "content": usuario}],
                output_config={
                    "effort": self._esforco,
                    "format": {"type": "json_schema", "schema": schema},
                },
                fallbacks="default",
                betas=[_FALLBACK_DE_RECUSA],
            )
        except anthropic.AnthropicError as erro:
            raise FalhaDoModelo(f"Anthropic: {erro}") from erro
        if resposta.stop_reason != "end_turn":
            raise FalhaDoModelo(f"Anthropic parou com stop_reason={resposta.stop_reason}")
        texto = next((bloco.text for bloco in resposta.content if bloco.type == "text"), "")
        try:
            return json.loads(texto)
        except json.JSONDecodeError as erro:
            raise FalhaDoModelo("Anthropic não devolveu JSON") from erro
