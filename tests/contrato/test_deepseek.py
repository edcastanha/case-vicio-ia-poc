import json
from types import SimpleNamespace

import httpx2
import openai
import pytest

from classificacao.adaptadores.deepseek_api import ModeloDeepSeek
from classificacao.aplicacao.portas import FalhaDoModelo
from classificacao.aplicacao.prompts import SCHEMA_DO_VOTO

VOTO = '{"no_id": 10, "confianca": 0.9, "justificativa": "j", "extras": []}'


def resposta(conteudo=VOTO, fim="stop"):
    mensagem = SimpleNamespace(content=conteudo, reasoning_content="raciocínio")
    uso = SimpleNamespace(prompt_tokens=1000, prompt_cache_hit_tokens=800, completion_tokens=200)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=mensagem, finish_reason=fim)], usage=uso
    )


class ClienteFalso:
    def __init__(self, devolver=None, erro=None):
        self.chamadas: list[dict] = []
        self._devolver, self._erro = devolver, erro
        completions = SimpleNamespace(create=self._criar)
        self.chat = SimpleNamespace(completions=completions)

    def _criar(self, **parametros):
        self.chamadas.append(parametros)
        if self._erro:
            raise self._erro
        return self._devolver or resposta()


def test_voto_em_json_mode_com_thinking_e_exemplo_do_formato_no_prompt():
    cliente = ClienteFalso()
    voto = ModeloDeepSeek("deepseek-v4-pro", cliente=cliente).responder(
        "SIS", "USU", SCHEMA_DO_VOTO
    )
    assert voto["no_id"] == 10
    [chamada] = cliente.chamadas
    assert chamada["model"] == "deepseek-v4-pro"
    assert chamada["response_format"] == {"type": "json_object"}
    assert chamada["reasoning_effort"] == "high"
    sistema, usuario = chamada["messages"]
    assert sistema == {"role": "system", "content": "SIS"}
    assert usuario["content"].startswith("USU")
    # o JSON mode do DeepSeek exige a palavra json e um exemplo do formato
    assert "json" in usuario["content"].lower()
    exemplo = usuario["content"][usuario["content"].index("{") :]
    assert set(json.loads(exemplo)) == set(SCHEMA_DO_VOTO["properties"])


@pytest.mark.parametrize(
    "cliente",
    [
        ClienteFalso(devolver=resposta(conteudo="")),
        ClienteFalso(devolver=resposta(fim="length")),
        ClienteFalso(devolver=resposta(fim="content_filter")),
        ClienteFalso(devolver=resposta(conteudo="não é json")),
        ClienteFalso(
            erro=openai.APIConnectionError(
                request=httpx2.Request("POST", "https://api.deepseek.com")
            )
        ),
    ],
    ids=["vazio", "cortada", "filtro", "json invalido", "erro do sdk"],
)
def test_falhas_do_deepseek_viram_falha_do_modelo(cliente):
    with pytest.raises(FalhaDoModelo):
        ModeloDeepSeek("deepseek-v4-pro", cliente=cliente).responder("s", "u", SCHEMA_DO_VOTO)


def test_soma_os_tokens_informados_pela_api_para_estimar_o_custo():
    modelo = ModeloDeepSeek("deepseek-flash", cliente=ClienteFalso())
    modelo.responder("s", "u", SCHEMA_DO_VOTO)
    modelo.responder("s", "u", SCHEMA_DO_VOTO)
    assert modelo.tokens == {"entrada_cache": 1600, "entrada_sem_cache": 400, "saida": 400}
