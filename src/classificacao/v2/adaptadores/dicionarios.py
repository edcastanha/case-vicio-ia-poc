import csv
from pathlib import Path

from classificacao.v2.dominio.leis import Lei


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
