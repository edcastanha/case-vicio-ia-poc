"""Amostra do enriquecimento para o autor revisar: onde um texto ruim custa mais."""

import re
from collections.abc import Mapping

from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.v2.dominio.temas import TemaEnriquecido

_CONTAGEM = re.compile(r"(\d+) questões no source")


def questoes_no_catalogo(no: No) -> int:
    """Quantas Questões o catálogo antigo diz que o Nó tem (a descrição automática conta)."""
    encontrado = _CONTAGEM.search(no.descricao)
    return int(encontrado.group(1)) if encontrado else 0


def amostra_para_revisao(arvore: Arvore, tamanho: int = 30) -> list[No]:
    """Todos os Nós de Temas duplicados, depois as maiores Lixeiras pela contagem do catálogo."""
    nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.caminho)
    duplicados = [no for no in nos if arvore.em_tema_duplicado(no.id) and no.nivel == 1]
    resto = sorted(
        (no for no in nos if no not in duplicados), key=lambda no: -questoes_no_catalogo(no)
    )
    return (duplicados + resto)[:tamanho]


def linhas_da_revisao(
    arvore: Arvore, amostra: list[No], temas: Mapping[int, TemaEnriquecido]
) -> list[dict[str, str]]:
    return [
        {
            "no_id": str(no.id),
            "caminho": no.caminho,
            "por_que_na_amostra": (
                "tema duplicado"
                if arvore.em_tema_duplicado(no.id)
                else f"lixeira ({questoes_no_catalogo(no)} no catálogo)"
            ),
            "descricao": temas[no.id].descricao,
            "nao_entra": temas[no.id].nao_entra,
            "termos": "; ".join(temas[no.id].termos),
            "leis": "; ".join(temas[no.id].leis),
            "ok": "",
            "correcao": "",
        }
        for no in amostra
    ]
