from types import SimpleNamespace

import pytest
from google.genai import errors, types

from classificacao.adaptadores.gemini_api import EmbeddingsGemini, ModeloGemini
from classificacao.aplicacao.portas import FalhaDoModelo
from classificacao.aplicacao.prompts import SCHEMA_DO_VOTO

VOTO = '{"no_id": 10, "confianca": 0.9, "justificativa": "j", "extras": []}'


def resposta(texto=VOTO, fim=types.FinishReason.STOP):
    return SimpleNamespace(text=texto, candidates=[SimpleNamespace(finish_reason=fim)])


class ClienteFalso:
    def __init__(self, devolver=None, erro=None, erros_no_embed=()):
        self.chamadas: list[dict] = []
        self._devolver, self._erro = devolver, erro
        self._erros_no_embed = list(erros_no_embed)
        self.models = SimpleNamespace(generate_content=self._gerar, embed_content=self._embutir)

    def _gerar(self, **parametros):
        self.chamadas.append(parametros)
        if self._erro:
            raise self._erro
        return self._devolver or resposta()

    def _embutir(self, **parametros):
        self.chamadas.append(parametros)
        if self._erros_no_embed:
            raise self._erros_no_embed.pop(0)
        n = len(parametros["contents"])
        return SimpleNamespace(
            embeddings=[SimpleNamespace(values=[float(i), 1.0]) for i in range(n)]
        )


def test_voto_com_sistema_e_schema_imposto():
    cliente = ClienteFalso()
    voto = ModeloGemini("gemini-3.8-flash", cliente=cliente).responder("SIS", "USU", SCHEMA_DO_VOTO)
    assert voto["no_id"] == 10
    [chamada] = cliente.chamadas
    assert chamada["model"] == "gemini-3.8-flash"
    assert chamada["contents"] == "USU"
    assert chamada["config"].system_instruction == "SIS"
    assert chamada["config"].response_mime_type == "application/json"
    assert chamada["config"].response_json_schema == SCHEMA_DO_VOTO
    assert ModeloGemini("gemini-3.8-flash", cliente=cliente).identificador == "api:gemini-3.8-flash"


@pytest.mark.parametrize(
    "cliente",
    [
        ClienteFalso(devolver=resposta(fim=types.FinishReason.SAFETY)),
        ClienteFalso(devolver=resposta(fim=types.FinishReason.MAX_TOKENS)),
        ClienteFalso(devolver=SimpleNamespace(text=None, candidates=[])),
        ClienteFalso(devolver=resposta(texto="não é json")),
        ClienteFalso(erro=errors.APIError(503, {"error": {"message": "sobrecarga"}})),
    ],
    ids=["bloqueio", "cortada", "sem candidatos", "json invalido", "erro do sdk"],
)
def test_falhas_do_gemini_viram_falha_do_modelo(cliente):
    with pytest.raises(FalhaDoModelo):
        ModeloGemini("gemini-3.8-flash", cliente=cliente).responder("s", "u", SCHEMA_DO_VOTO)


def test_embeddings_um_vetor_por_texto_cada_um_em_seu_content():
    cliente = ClienteFalso()
    vetores = EmbeddingsGemini(cliente=cliente).vetorizar(["a", "b", "c"])
    assert len(vetores) == 3
    [chamada] = cliente.chamadas
    assert chamada["model"] == "gemini-embedding-2"
    assert all(isinstance(c, types.Content) for c in chamada["contents"])
    assert chamada["contents"][1].parts[0].text.endswith("b")
    assert chamada["config"].output_dimensionality == 768


def cota_estourada(espera: str | None = "33s") -> errors.ClientError:
    detalhes = (
        []
        if espera is None
        else [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": espera}]
    )
    erro = {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": detalhes}
    return errors.ClientError(429, {"error": erro})


def test_embeddings_com_cota_por_minuto_estourada_esperam_o_tempo_pedido_e_tentam_de_novo():
    esperas: list[float] = []
    cliente = ClienteFalso(erros_no_embed=[cota_estourada("33s"), cota_estourada(None)])
    vetores = EmbeddingsGemini(cliente=cliente, esperar=esperas.append).vetorizar(["a", "b"])
    assert len(vetores) == 2
    assert esperas == [34.0, 61.0]  # o pedido pela API (+1s), ou um minuto se ela não disser


def test_embeddings_desistem_depois_das_tentativas_e_viram_falha_do_modelo():
    cliente = ClienteFalso(erros_no_embed=[cota_estourada()] * 5)
    embeddings = EmbeddingsGemini(cliente=cliente, esperar=lambda segundos: None, tentativas=3)
    with pytest.raises(FalhaDoModelo, match="429"):
        embeddings.vetorizar(["a"])
    assert len(cliente.chamadas) == 3


def test_embeddings_com_outro_erro_do_sdk_falham_sem_esperar():
    esperas: list[float] = []
    erro = errors.APIError(503, {"error": {"message": "sobrecarga"}})
    cliente = ClienteFalso(erros_no_embed=[erro])
    with pytest.raises(FalhaDoModelo):
        EmbeddingsGemini(cliente=cliente, esperar=esperas.append).vetorizar(["a"])
    assert esperas == []
