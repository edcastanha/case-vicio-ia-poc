"""Carrega os artefatos versionados de dados/v2/ (sem rede e sem modelo)."""

from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore
from classificacao.v2.adaptadores import cache_de_embeddings
from classificacao.v2.adaptadores.dicionarios import ler_leis, ler_temas_enriquecidos
from classificacao.v2.aplicacao.montar_sinais import Conhecimento, Vetores, montar_sinais

DADOS = Path("dados/v2")


def carregar_conhecimento(zip_anexos: Path, modelo: str) -> Conhecimento:
    pasta = DADOS / "embeddings" / modelo
    ids_q, matriz_q, _ = cache_de_embeddings.ler(pasta, "questoes")
    ids_n, matriz_n, _ = cache_de_embeddings.ler(pasta, "nos")
    return Conhecimento(
        arvore=ler_arvore(zip_anexos),
        leis=ler_leis(DADOS / "leis.csv"),
        temas=ler_temas_enriquecidos(DADOS / "temas_enriquecidos.jsonl"),
        questoes=Vetores(ids_q, matriz_q),
        nos=Vetores(ids_n, matriz_n),
    )


def montador(conhecimento: Conhecimento):
    """`montar(questoes, rotuladas)` sobre um Conhecimento: a forma que a validação usa."""

    def montar(questoes, rotuladas):
        return montar_sinais(questoes, conhecimento, rotuladas)

    return montar
