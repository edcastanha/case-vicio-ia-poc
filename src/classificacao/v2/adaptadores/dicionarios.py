import csv
import json
from pathlib import Path

from classificacao.v2.dominio.leis import Lei
from classificacao.v2.dominio.temas import TemaEnriquecido


def ler_leis(caminho: Path) -> list[Lei]:
    """dados/v2/leis.csv: número, nome, apelidos e Nós de cada lei, separados por `;`."""
    with caminho.open(newline="") as arquivo:
        return [
            Lei(
                numero=linha["numero"],
                nome=linha["nome"],
                apelidos=tuple(a for a in linha["apelidos"].split(";") if a),
                nos=tuple(int(no) for no in linha["nos"].split(";") if no),
            )
            for linha in csv.DictReader(arquivo)
        ]


def ler_temas_enriquecidos(caminho: Path) -> dict[int, TemaEnriquecido]:
    """dados/v2/temas_enriquecidos.jsonl: um Nó por linha; vazio se o arquivo não existe."""
    if not caminho.exists():
        return {}
    temas = {}
    for linha in caminho.read_text().splitlines():
        if linha.strip():
            bruto = json.loads(linha)
            temas[bruto["no_id"]] = TemaEnriquecido(
                no_id=bruto["no_id"],
                descricao=bruto["descricao"],
                nao_entra=bruto["nao_entra"],
                termos=tuple(bruto["termos"]),
                leis=tuple(bruto["leis"]),
                prompt=bruto["prompt"],
            )
    return temas


def ler_correcoes_dos_temas(caminho: Path) -> dict[int, dict[str, object]]:
    """dados/v2/correcoes_dos_temas.jsonl: as correções aceitas na revisão; vazio se não há."""
    if not caminho.exists():
        return {}
    correcoes = {}
    for linha in caminho.read_text().splitlines():
        if linha.strip():
            bruto = json.loads(linha)
            correcoes[bruto["no_id"]] = bruto["correcoes"]
    return correcoes
