"""Raiz de composição: lê o .env e monta os papéis com o backend e o modelo de cada um."""

import os
from pathlib import Path

from classificacao.adaptadores.anthropic_api import ModeloAnthropic
from classificacao.adaptadores.claude_code import ModeloClaudeCode
from classificacao.aplicacao.classificar_questao import Papeis
from classificacao.aplicacao.portas import ModeloDeLinguagem

# Q15 (modo api) e Q21 (modo claude-code): modelos diferentes por papel.
MODELO_PADRAO = {
    ("classificador", "api"): "claude-sonnet-5-5",
    ("verificador", "api"): "gemini-3.8-flash",
    ("juiz", "api"): "deepseek-v4-pro",
    ("classificador", "claude-code"): "sonnet",
    ("verificador", "claude-code"): "opus",
    ("juiz", "claude-code"): "opus",
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
        juiz=criar_modelo("juiz"),
    )


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
    raise SystemExit(f"backend api ainda sem adaptador para o modelo {modelo!r} ({papel})")
