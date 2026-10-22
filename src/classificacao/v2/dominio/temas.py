from collections.abc import Mapping
from dataclasses import dataclass, replace

from classificacao.nucleo.dominio.arvore import Arvore, No


@dataclass(frozen=True)
class TemaEnriquecido:
    """Descrição de um Nó gerada antes da decisão, a partir só da Árvore de temas."""

    no_id: int
    descricao: str
    nao_entra: str
    termos: tuple[str, ...]
    leis: tuple[str, ...]
    prompt: str = ""  # rótulo da versão do prompt que gerou o texto: enriquecedor/v1@hash


CAMPOS_CORRIGIVEIS = ("descricao", "nao_entra", "termos", "leis")


def corrigir(
    temas: Mapping[int, TemaEnriquecido], correcoes: Mapping[int, Mapping[str, object]]
) -> dict[int, TemaEnriquecido]:
    """Aplica as correções aceitas na revisão; o rótulo do enriquecimento fica como estava."""
    corrigidos = dict(temas)
    for no_id, campos in correcoes.items():
        if no_id not in temas:
            raise ValueError(f"correção para o Nó {no_id}, que não tem tema enriquecido")
        estranhos = set(campos) - set(CAMPOS_CORRIGIVEIS)
        if estranhos:
            raise ValueError(f"campos que a revisão não corrige: {sorted(estranhos)}")
        novos = {
            campo: tuple(valor) if campo in ("termos", "leis") else valor
            for campo, valor in campos.items()
        }
        corrigidos[no_id] = replace(temas[no_id], **novos)
    return corrigidos


def texto_do_tema(no: No, tema: TemaEnriquecido | None) -> str:
    """O que representa o Nó nos embeddings e na busca: caminho mais o texto enriquecido."""
    if tema is None:
        return no.caminho
    return "\n".join(
        [
            no.caminho,
            tema.descricao,
            f"Termos: {', '.join(tema.termos)}",
            f"Leis: {', '.join(tema.leis)}",
        ]
    )


def contexto_da_arvore(arvore: Arvore) -> str:
    """A Árvore inteira, um Nó por linha (`[id] caminho`), para o modelo ver os vizinhos."""
    nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.caminho)
    return "\n".join(f"[{no.id}] {no.caminho}" for no in nos)
