import tomllib
from collections.abc import Mapping
from pathlib import Path

from classificacao.aplicacao.prompts import Prompt, PromptsDosPapeis

PAPEIS = ("classificador", "verificador", "juiz")


class PromptInexistente(FileNotFoundError):
    pass


def ler_versoes_ativas(pasta: Path) -> dict[str, str]:
    """Versão ativa de cada papel, em prompts/versoes.toml; os três do pipeline são obrigatórios."""
    versoes = tomllib.loads((pasta / "versoes.toml").read_text())
    faltando = [papel for papel in PAPEIS if papel not in versoes]
    if faltando:
        raise PromptInexistente(f"versoes.toml sem versão para: {', '.join(faltando)}")
    return {papel: str(versao) for papel, versao in versoes.items()}


def carregar_prompts(pasta: Path, versoes: Mapping[str, str]) -> PromptsDosPapeis:
    return PromptsDosPapeis(*(carregar_prompt(pasta, papel, versoes[papel]) for papel in PAPEIS))


def carregar_prompt(pasta: Path, papel: str, versao: str) -> Prompt:
    arquivo = pasta / papel / f"{versao}.md"
    if not arquivo.exists():
        raise PromptInexistente(f"prompt não encontrado: {papel}/{versao}.md em {pasta}")
    return Prompt(papel, versao, arquivo.read_text())
