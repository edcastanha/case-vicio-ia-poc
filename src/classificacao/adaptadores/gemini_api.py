import json
import re
import time
from collections.abc import Callable

from google import genai
from google.genai import errors, types

from classificacao.aplicacao.portas import FalhaDoModelo


class ModeloGemini:
    """Verificador no backend api: generateContent com JSON imposto pelo schema."""

    def __init__(self, modelo: str, cliente: genai.Client | None = None) -> None:
        self.modelo = modelo
        self.identificador = f"api:{modelo}"
        self._cliente = cliente or genai.Client()

    def responder(self, sistema: str, usuario: str, schema: dict) -> dict:
        try:
            resposta = self._cliente.models.generate_content(
                model=self.modelo,
                contents=usuario,
                config=types.GenerateContentConfig(
                    system_instruction=sistema,
                    response_mime_type="application/json",
                    response_json_schema=schema,
                ),
            )
        except errors.APIError as erro:
            raise FalhaDoModelo(f"Gemini: {erro}") from erro
        if not resposta.candidates:
            raise FalhaDoModelo("Gemini não devolveu candidatos (prompt bloqueado?)")
        fim = resposta.candidates[0].finish_reason
        if fim != types.FinishReason.STOP:
            raise FalhaDoModelo(f"Gemini parou com finish_reason={fim}")
        try:
            return json.loads(resposta.text or "")
        except json.JSONDecodeError as erro:
            raise FalhaDoModelo("Gemini não devolveu JSON") from erro


class EmbeddingsGemini:
    """gemini-embedding-2: cada texto vai num Content próprio, senão sai um vetor agregado."""

    def __init__(
        self,
        modelo: str = "gemini-embedding-2",
        dimensoes: int = 768,
        cliente: genai.Client | None = None,
        esperar: Callable[[float], None] = time.sleep,
        tentativas: int = 4,
    ) -> None:
        self._modelo = modelo
        self._dimensoes = dimensoes
        self._cliente = cliente or genai.Client()
        self._esperar = esperar
        self._tentativas = tentativas

    def vetorizar(self, textos: list[str]) -> list[list[float]]:
        # O v2 não aceita task_type: a tarefa vai no próprio texto.
        conteudos = [
            types.Content(
                parts=[types.Part.from_text(text=f"task: sentence similarity | query: {t}")]
            )
            for t in textos
        ]
        resultado = self._embutir(conteudos)
        if len(resultado.embeddings) != len(textos):
            raise FalhaDoModelo(
                f"embeddings: {len(resultado.embeddings)} vetores para {len(textos)} textos"
            )
        return [list(embedding.values) for embedding in resultado.embeddings]

    def _embutir(self, conteudos: list[types.Content]):
        """A cota gratuita é por minuto (100 textos): no 429, espera o que a API pedir."""
        for tentativa in range(1, self._tentativas + 1):
            try:
                return self._cliente.models.embed_content(
                    model=self._modelo,
                    contents=conteudos,
                    config=types.EmbedContentConfig(output_dimensionality=self._dimensoes),
                )
            except errors.APIError as erro:
                if erro.code != 429 or tentativa == self._tentativas:
                    raise FalhaDoModelo(f"Gemini embeddings: {erro}") from erro
                self._esperar(_espera_pedida(erro) + 1)
        raise AssertionError("inalcançável")


def _espera_pedida(erro: errors.APIError) -> float:
    """Segundos do RetryInfo da resposta, ou um minuto se a API não disser."""
    for detalhe in (erro.details or {}).get("error", {}).get("details", []):
        atraso = re.fullmatch(r"([\d.]+)s", str(detalhe.get("retryDelay", "")))
        if atraso:
            return float(atraso.group(1))
    return 60.0
