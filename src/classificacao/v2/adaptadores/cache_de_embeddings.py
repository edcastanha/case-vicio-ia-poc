"""Vetores versionados em dados/v2/embeddings/<modelo>/: uma matriz por parte e o manifesto."""

import hashlib
import json
from pathlib import Path

import numpy as np


def sha256_dos_textos(textos: list[str]) -> str:
    return hashlib.sha256("\x1e".join(textos).encode()).hexdigest()


def gravar(pasta: Path, parte: str, ids: list, vetores: np.ndarray, manifesto: dict) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    np.save(pasta / f"{parte}.npy", vetores)
    (pasta / f"{parte}.ids.json").write_text(json.dumps(ids))
    (pasta / f"{parte}.manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n"
    )


def ler(pasta: Path, parte: str) -> tuple[list, np.ndarray, dict]:
    ids = json.loads((pasta / f"{parte}.ids.json").read_text())
    vetores = np.load(pasta / f"{parte}.npy")
    manifesto = json.loads((pasta / f"{parte}.manifesto.json").read_text())
    if len(ids) != len(vetores):
        raise ValueError(f"{pasta}/{parte}: {len(ids)} ids para {len(vetores)} vetores")
    return ids, vetores, manifesto
