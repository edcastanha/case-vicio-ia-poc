import json
import subprocess
from pathlib import Path

import pytest

from classificacao.adaptadores.claude_code import ModeloClaudeCode
from classificacao.aplicacao.portas import FalhaDoModelo
from classificacao.aplicacao.prompts import SCHEMA_DO_VOTO

ENVELOPE = (Path(__file__).parent / "gravacoes" / "claude_code_envelope.json").read_text()


class ExecutorGravado:
    def __init__(self, stdout: str = ENVELOPE, codigo: int = 0, erro: Exception | None = None):
        self.stdout, self.codigo, self.erro = stdout, codigo, erro
        self.comando: list[str] = []
        self.entrada = ""

    def __call__(self, comando, input, capture_output, text, timeout):
        self.comando, self.entrada = comando, input
        if self.erro:
            raise self.erro
        return subprocess.CompletedProcess(comando, self.codigo, self.stdout, "stderr")


def test_le_o_voto_estruturado_do_envelope_gravado():
    modelo = ModeloClaudeCode("haiku", executar=ExecutorGravado())
    resposta = modelo.responder("sistema", "usuario", SCHEMA_DO_VOTO)
    assert resposta["no_id"] == 10
    assert resposta["confianca"] == 0.9


def test_comando_usa_modelo_schema_e_sistema_sem_ferramentas_e_prompt_pela_entrada():
    executor = ExecutorGravado()
    ModeloClaudeCode("sonnet", executar=executor).responder("SISTEMA", "PROMPT", SCHEMA_DO_VOTO)
    comando = executor.comando
    assert comando[:2] == ["claude", "-p"]
    assert comando[comando.index("--model") + 1] == "sonnet"
    assert json.loads(comando[comando.index("--json-schema") + 1]) == SCHEMA_DO_VOTO
    assert comando[comando.index("--system-prompt") + 1] == "SISTEMA"
    assert comando[comando.index("--tools") + 1] == ""
    assert "--no-session-persistence" in comando
    assert executor.entrada == "PROMPT"
    assert "PROMPT" not in comando


def test_identificador_separa_backend_e_modelo_para_o_cache():
    assert ModeloClaudeCode("sonnet").identificador == "claude-code:sonnet"


@pytest.mark.parametrize(
    "executor",
    [
        ExecutorGravado(stdout=json.dumps({"is_error": True, "subtype": "error", "result": "x"})),
        ExecutorGravado(codigo=1),
        ExecutorGravado(stdout="não é json"),
        ExecutorGravado(erro=subprocess.TimeoutExpired("claude", 600)),
    ],
    ids=["envelope de erro", "codigo de saida", "saida invalida", "timeout"],
)
def test_falhas_do_claude_code_viram_falha_do_modelo(executor):
    with pytest.raises(FalhaDoModelo):
        ModeloClaudeCode("haiku", executar=executor).responder("s", "u", SCHEMA_DO_VOTO)


def test_soma_o_custo_informado_pelos_envelopes():
    modelo = ModeloClaudeCode("haiku", executar=ExecutorGravado())
    modelo.responder("s", "u", SCHEMA_DO_VOTO)
    modelo.responder("s", "u", SCHEMA_DO_VOTO)
    assert modelo.custo_usd == pytest.approx(2 * 0.0004469, rel=1e-3)
