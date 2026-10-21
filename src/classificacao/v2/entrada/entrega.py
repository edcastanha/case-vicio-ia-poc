"""`classificacao v2 entrega`: regenera publicacao.csv e previsao.txt sem rede e sem modelo.

Só lê os anexos e os artefatos versionados em dados/v2/; nenhum adaptador de modelo de
linguagem nem de embeddings é importado aqui (tests/v2/contrato/test_entrega_sem_modelo.py).
"""

import csv
import json
import time
from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_folha_verdade, ler_questoes
from classificacao.v2.aplicacao.gerar_entrega import gerar_entrega, texto_da_previsao
from classificacao.v2.dominio.decisao import ALVO
from classificacao.v2.entrada.conhecimento import DADOS, carregar_conhecimento, montador

ESCOLHA = DADOS / "escolha.json"  # Ranqueador e embeddings escolhidos pela comparação


def rodar(zip_anexos: Path, saida: Path, repeticoes: int) -> None:
    inicio = time.perf_counter()
    escolha = json.loads(ESCOLHA.read_text())
    conhecimento = carregar_conhecimento(zip_anexos, escolha["embeddings"])
    entrega = gerar_entrega(
        ler_questoes(zip_anexos),
        conhecimento.arvore,
        ler_folha_verdade(zip_anexos),
        montador(conhecimento),
        escolha["ranqueador"],
        ALVO,
        repeticoes=repeticoes,
    )
    saida.mkdir(parents=True, exist_ok=True)
    with (saida / "publicacao.csv").open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(entrega.linhas[0]))
        escritor.writeheader()
        escritor.writerows(entrega.linhas)
    texto = texto_da_previsao(entrega.previsao, escolha["ranqueador"], escolha["embeddings"])
    (saida / "previsao.txt").write_text(texto)
    print(texto.split("\n\n")[0])
    print(f"{len(entrega.linhas)} Questões em {time.perf_counter() - inicio:.1f}s")
