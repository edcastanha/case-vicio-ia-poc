import json
import os

import openai

from classificacao.aplicacao.portas import FalhaDoModelo

_URL = "https://api.deepseek.com"


class ModeloDeepSeek:
    """Juiz no backend api: JSON mode (sem schema imposto) com thinking ligado."""

    def __init__(
        self, modelo: str, cliente: openai.OpenAI | None = None, esforco: str = "high"
    ) -> None:
        self.modelo = modelo
        self.identificador = f"api:{modelo}"
        self._cliente = cliente or openai.OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url=_URL
        )
        self._esforco = esforco

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict:
        try:
            resposta = self._cliente.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": f"{usuario}\n\n{_instrucao_json(schema)}"},
                ],
                response_format={"type": "json_object"},
                reasoning_effort=self._esforco,
            )
        except openai.APIError as erro:
            raise FalhaDoModelo(f"DeepSeek: {erro}") from erro
        escolha = resposta.choices[0]
        if escolha.finish_reason != "stop":
            raise FalhaDoModelo(f"DeepSeek parou com finish_reason={escolha.finish_reason}")
        # A doc avisa que o JSON mode às vezes devolve conteúdo vazio: vira falha e o retry age.
        try:
            return json.loads(escolha.message.content or "")
        except json.JSONDecodeError as erro:
            raise FalhaDoModelo("DeepSeek não devolveu JSON") from erro


def _instrucao_json(schema: dict) -> str:
    """O JSON mode do DeepSeek exige a palavra json e um exemplo do formato no prompt."""
    exemplo = {"no_id": 123, "confianca": 0.8, "justificativa": "...", "extras": []}
    exemplo = {campo: exemplo.get(campo, "...") for campo in schema["properties"]}
    return (
        "Responda apenas com um objeto json neste formato "
        f"(no_id pode ser null): {json.dumps(exemplo, ensure_ascii=False)}"
    )
