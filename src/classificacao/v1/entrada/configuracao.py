"""Raiz de composição: lê o .env e monta os papéis com o backend, o modelo e o prompt de cada um."""

import os
from pathlib import Path

from classificacao.v1.adaptadores.anthropic_api import ModeloAnthropic
from classificacao.v1.adaptadores.claude_code import ModeloClaudeCode
from classificacao.v1.adaptadores.deepseek_api import ModeloDeepSeek
from classificacao.v1.adaptadores.gemini_api import EmbeddingsGemini, ModeloGemini
from classificacao.v1.adaptadores.prompts_em_arquivo import (
    PAPEIS,
    carregar_prompt,
    carregar_prompts,
    ler_versoes_ativas,
)
from classificacao.v1.aplicacao.classificar_questao import Papeis
from classificacao.v1.aplicacao.portas import Embeddings, ModeloDeLinguagem
from classificacao.v1.aplicacao.prompts import Prompt, PromptsDosPapeis

PASTA_DE_PROMPTS = Path("prompts/v1")

# Q15 (modo api) e Q21 (modo claude-code): modelos diferentes por papel.
MODELO_PADRAO = {
    ("classificador", "api"): "claude-sonnet-5-5",
    ("verificador", "api"): "gemini-3.8-flash",
    ("desempatador", "api"): "deepseek-v4-pro",
    ("classificador", "claude-code"): "sonnet",
    ("verificador", "claude-code"): "opus",
    ("desempatador", "claude-code"): "opus",
    # ADR 0004: o Rotulador é o modelo mais forte disponível, fora dos papéis do pipeline.
    ("rotulador", "api"): "claude-opus-5-5",
    ("rotulador", "claude-code"): "opus",
}


def carregar_env(caminho: Path = Path(".env")) -> None:
    """Carrega KEY=valor do .env sem sobrescrever o que já está no ambiente."""
    if not caminho.exists():
        return
    for linha in caminho.read_text().splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.split("#", 1)[0].strip().strip("\"'"))


def criar_papeis() -> Papeis:
    return Papeis(
        classificador=criar_modelo("classificador"),
        verificador=criar_modelo("verificador"),
        desempatador=criar_modelo("desempatador"),
    )


def criar_prompts(pasta: Path = PASTA_DE_PROMPTS) -> PromptsDosPapeis:
    """Versão ativa de prompts/v1/versoes.toml; <PAPEL>_PROMPT no .env troca a de um papel."""
    versoes = ler_versoes_ativas(pasta)
    for papel in PAPEIS:
        versoes[papel] = os.environ.get(f"{papel.upper()}_PROMPT") or versoes[papel]
    return carregar_prompts(pasta, versoes)


def criar_prompt_do_rotulador(pasta: Path = PASTA_DE_PROMPTS) -> Prompt:
    versao = os.environ.get("ROTULADOR_PROMPT") or ler_versoes_ativas(pasta).get("rotulador")
    if versao is None:
        raise SystemExit("prompts/v1/versoes.toml sem versão para o rotulador")
    return carregar_prompt(pasta, "rotulador", versao)


def criar_modelo(papel: str) -> ModeloDeLinguagem:
    backend = os.environ.get(f"{papel.upper()}_BACKEND", "claude-code")
    modelo = os.environ.get(f"{papel.upper()}_MODELO") or MODELO_PADRAO[(papel, backend)]
    if backend == "claude-code":
        return ModeloClaudeCode(modelo)
    if backend == "api":
        return _modelo_api(papel, modelo)
    raise SystemExit(f"{papel.upper()}_BACKEND inválido: {backend!r} (use api ou claude-code)")


def _modelo_api(papel: str, modelo: str) -> ModeloDeLinguagem:
    if modelo.startswith("claude-"):
        return ModeloAnthropic(modelo)
    if modelo.startswith("gemini-"):
        return ModeloGemini(modelo)
    if modelo.startswith("deepseek-"):
        return ModeloDeepSeek(modelo)
    raise SystemExit(f"backend api ainda sem adaptador para o modelo {modelo!r} ({papel})")


def criar_embeddings() -> Embeddings:
    return EmbeddingsGemini(modelo=os.environ.get("EMBEDDINGS_MODELO", "gemini-embedding-2"))
