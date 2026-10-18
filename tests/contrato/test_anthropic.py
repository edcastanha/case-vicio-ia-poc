from types import SimpleNamespace

import anthropic
import pytest

from classificacao.adaptadores.anthropic_api import ModeloAnthropic
from classificacao.aplicacao.portas import FalhaDoModelo
from classificacao.aplicacao.prompts import SCHEMA_DO_VOTO

VOTO = '{"no_id": 10, "confianca": 0.9, "justificativa": "j", "extras": []}'


def resposta(texto: str = VOTO, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text=texto),
        ],
    )


class ClienteFalso:
    def __init__(self, devolver=None, erro: Exception | None = None):
        self.chamadas: list[dict] = []
        self._devolver, self._erro = devolver or resposta(), erro
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **parametros):
        self.chamadas.append(parametros)
        if self._erro:
            raise self._erro
        return self._devolver


def test_le_o_voto_do_bloco_de_texto():
    modelo = ModeloAnthropic("claude-sonnet-5-5", cliente=ClienteFalso())
    assert modelo.responder("s", "u", SCHEMA_DO_VOTO)["no_id"] == 10


def test_chamada_impoe_o_schema_cacheia_o_sistema_e_liga_o_fallback_de_recusa():
    cliente = ClienteFalso()
    ModeloAnthropic("claude-sonnet-5-5", cliente=cliente, esforco="high").responder(
        "SISTEMA", "PROMPT", SCHEMA_DO_VOTO
    )
    [chamada] = cliente.chamadas
    assert chamada["model"] == "claude-sonnet-5-5"
    assert chamada["system"] == [
        {"type": "text", "text": "SISTEMA", "cache_control": {"type": "ephemeral", "ttl": "1h"}}
    ]
    assert chamada["messages"] == [{"role": "user", "content": "PROMPT"}]
    assert chamada["output_config"] == {
        "effort": "high",
        "format": {"type": "json_schema", "schema": SCHEMA_DO_VOTO},
    }
    assert chamada["fallbacks"] == "default"
    assert chamada["betas"] == ["server-side-fallback-2026-07-01"]


def test_identificador_separa_backend_e_modelo():
    assert ModeloAnthropic("claude-sonnet-5-5", cliente=ClienteFalso()).identificador == (
        "api:claude-sonnet-5-5"
    )


@pytest.mark.parametrize(
    "cliente",
    [
        ClienteFalso(devolver=resposta(stop_reason="refusal")),
        ClienteFalso(devolver=resposta(stop_reason="max_tokens")),
        ClienteFalso(devolver=resposta(texto="não é json")),
        ClienteFalso(erro=anthropic.AnthropicError("fora do ar")),
    ],
    ids=["recusa", "cortada", "json invalido", "erro do sdk"],
)
def test_falhas_da_api_viram_falha_do_modelo(cliente):
    with pytest.raises(FalhaDoModelo):
        ModeloAnthropic("claude-sonnet-5-5", cliente=cliente).responder("s", "u", SCHEMA_DO_VOTO)
