"""Ponto de entrada: `classificacao v1 <comando>` ou `classificacao v2 <comando>`.

Cada versão do case tem a sua CLI; este módulo só escolhe qual delas recebe os argumentos.
"""

import importlib
import sys

CLI_DA_VERSAO = {"v1": "classificacao.v1.entrada.cli", "v2": "classificacao.v2.entrada.cli"}


def main(argv: list[str] | None = None) -> None:
    argumentos = sys.argv[1:] if argv is None else argv
    if not argumentos or argumentos[0] not in CLI_DA_VERSAO:
        raise SystemExit(f"uso: classificacao {{{','.join(CLI_DA_VERSAO)}}} <comando> [opções]")
    versao, resto = argumentos[0], argumentos[1:]
    importlib.import_module(CLI_DA_VERSAO[versao]).main(resto)
