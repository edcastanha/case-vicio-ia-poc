"""Embeddings com modelos abertos rodando na CPU; só para gerar o cache versionado.

A classificação nunca carrega estes modelos: ela lê os vetores de dados/v2/embeddings/.
Requer o grupo de dependências `embeddings` (`uv sync --group embeddings`).
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ModeloDeEmbeddings:
    nome: str  # como aparece em dados/v2/embeddings/<nome>/
    repositorio: str  # id no Hugging Face
    prefixo_da_questao: str = ""
    prefixo_do_tema: str = ""
    tamanho_maximo: int = 1024  # tokens; o resto do texto é cortado


MODELOS = {
    "bge-m3": ModeloDeEmbeddings("bge-m3", "BAAI/bge-m3"),
    # O e5 foi treinado com prefixos: a Questão é a consulta e o Tema, a passagem.
    "e5-base": ModeloDeEmbeddings(
        "e5-base", "intfloat/multilingual-e5-base", "query: ", "passage: ", 512
    ),
}


def vetorizar(modelo: ModeloDeEmbeddings, textos: list[str], prefixo: str) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    carregado = SentenceTransformer(modelo.repositorio, device="cpu")
    carregado.max_seq_length = modelo.tamanho_maximo
    vetores = carregado.encode(
        [prefixo + texto for texto in textos],
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return vetores.astype(np.float32)


def revisao(modelo: ModeloDeEmbeddings) -> str:
    """Commit do modelo no Hugging Face, para o manifesto dizer exatamente qual pesos geraram."""
    from huggingface_hub import model_info

    return model_info(modelo.repositorio).sha or ""
