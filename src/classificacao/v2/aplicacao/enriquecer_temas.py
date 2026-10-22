import hashlib
import json
from collections.abc import Callable, Iterable, Sequence

from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.v2.aplicacao.portas import FalhaDoModelo, ModeloDeLinguagem
from classificacao.v2.dominio.temas import TemaEnriquecido, contexto_da_arvore

SCHEMA = {
    "type": "object",
    "properties": {
        "nos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "descricao": {"type": "string"},
                    "nao_entra": {"type": "string"},
                    "termos": {"type": "array", "items": {"type": "string"}},
                    "leis": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "descricao", "nao_entra", "termos", "leis"],
            },
        }
    },
    "required": ["nos"],
}


def rotulo_do_prompt(texto: str, versao: str) -> str:
    return f"enriquecedor/{versao}@{hashlib.sha256(texto.encode()).hexdigest()[:8]}"


def lotes_por_tema(arvore: Arvore, tamanho: int) -> list[list[No]]:
    """Nós em ordem de caminho, para que um lote tenha o Tema e os seus Subtemas juntos."""
    nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.caminho)
    return [nos[i : i + tamanho] for i in range(0, len(nos), tamanho)]


def enriquecer_temas(
    arvore: Arvore,
    modelo: ModeloDeLinguagem,
    prompt: str,
    rotulo: str,
    ja_feitos: Iterable[int],
    guardar: Callable[[list[TemaEnriquecido]], None],
    tamanho_do_lote: int = 20,
    tentativas: int = 3,
) -> list[int]:
    """Descreve os Nós que faltam, lote a lote; devolve os ids dos lotes que falharam."""
    feitos = set(ja_feitos)
    contexto = contexto_da_arvore(arvore)
    falhas: list[int] = []
    for lote in lotes_por_tema(arvore, tamanho_do_lote):
        pedidos = [no for no in lote if no.id not in feitos]
        if not pedidos:
            continue
        usuario = f"## Árvore\n{contexto}\n\n## Nós a descrever\n" + "\n".join(
            f"[{no.id}] {no.caminho}" for no in pedidos
        )
        for tentativa in range(1, tentativas + 1):
            try:
                resposta = modelo.responder(prompt, usuario, SCHEMA)
                guardar(_temas(resposta, pedidos, rotulo))
                break
            except FalhaDoModelo:
                if tentativa == tentativas:
                    falhas.extend(no.id for no in pedidos)
    return falhas


def _temas(resposta: dict, pedidos: Sequence[No], rotulo: str) -> list[TemaEnriquecido]:
    try:
        itens = {int(item["id"]): item for item in resposta["nos"]}
        temas = [
            TemaEnriquecido(
                no_id=no.id,
                descricao=str(itens[no.id]["descricao"]).strip(),
                nao_entra=str(itens[no.id]["nao_entra"]).strip(),
                termos=tuple(str(t).strip().casefold() for t in itens[no.id]["termos"]),
                leis=tuple(str(lei).strip() for lei in itens[no.id]["leis"]),
                prompt=rotulo,
            )
            for no in pedidos
        ]
    except (KeyError, TypeError, ValueError) as erro:
        raise FalhaDoModelo(f"resposta do enriquecedor malformada: {erro!r}") from erro
    if set(itens) - {no.id for no in pedidos}:
        raise FalhaDoModelo("o enriquecedor devolveu Nós que não foram pedidos")
    if any(not t.descricao or not t.termos for t in temas):
        raise FalhaDoModelo("o enriquecedor devolveu Nó sem descrição ou sem termos")
    return temas


def para_json(tema: TemaEnriquecido) -> str:
    return json.dumps(
        {
            "no_id": tema.no_id,
            "descricao": tema.descricao,
            "nao_entra": tema.nao_entra,
            "termos": list(tema.termos),
            "leis": list(tema.leis),
            "prompt": tema.prompt,
        },
        ensure_ascii=False,
    )
