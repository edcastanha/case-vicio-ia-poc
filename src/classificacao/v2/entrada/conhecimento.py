"""Carrega os artefatos versionados de dados/v2/ (sem rede e sem modelo)."""

from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore
from classificacao.v2.adaptadores import cache_de_embeddings
from classificacao.v2.adaptadores.dicionarios import (
    ler_correcoes_dos_temas,
    ler_leis,
    ler_temas_enriquecidos,
)
from classificacao.v2.aplicacao.montar_sinais import Conhecimento, Vetores, montar_sinais
from classificacao.v2.dominio.temas import TemaEnriquecido, corrigir

DADOS = Path("dados/v2")
CORRECOES_DOS_TEMAS = "correcoes_dos_temas.jsonl"


def temas_revisados() -> dict[int, TemaEnriquecido]:
    """Os Temas enriquecidos com as correções aceitas na revisão (dados/v2/revisao_temas.csv)."""
    return corrigir(
        ler_temas_enriquecidos(DADOS / "temas_enriquecidos.jsonl"),
        ler_correcoes_dos_temas(DADOS / CORRECOES_DOS_TEMAS),
    )


def carregar_conhecimento(zip_anexos: Path, modelo: str) -> Conhecimento:
    pasta = DADOS / "embeddings" / modelo
    ids_q, matriz_q, _ = cache_de_embeddings.ler(pasta, "questoes")
    ids_n, matriz_n, _ = cache_de_embeddings.ler(pasta, "nos")
    return Conhecimento(
        arvore=ler_arvore(zip_anexos),
        leis=ler_leis(DADOS / "leis.csv"),
        temas=temas_revisados(),
        questoes=Vetores(ids_q, matriz_q),
        nos=Vetores(ids_n, matriz_n),
    )


def montador(conhecimento: Conhecimento):
    """`montar(questoes, rotuladas)` sobre um Conhecimento: a forma que a validação usa."""

    def montar(questoes, rotuladas):
        return montar_sinais(questoes, conhecimento, rotuladas)

    return montar
