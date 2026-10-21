from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.v1.dominio.decisao import Voto

_PESO_CONFIANCA_DECLARADA = 0.5
_PESO_SIMILARIDADE = 0.4
_MAXIMO = 2 + _PESO_CONFIANCA_DECLARADA + _PESO_SIMILARIDADE


# Concordância domina: os outros sinais somados (0,9) nunca alcançam um degrau dela (1).
def pontuar(arvore: Arvore, classificador: Voto, verificador: Voto, similaridade: float) -> float:
    consenso = arvore.no_de_consenso(classificador.no_id, verificador.no_id)
    if consenso is None:
        concordancia = 0
    elif classificador.no_id == verificador.no_id:
        concordancia = 2
    else:
        concordancia = 1
    confianca_declarada = (classificador.confianca + verificador.confianca) / 2
    bruta = (
        concordancia
        + _PESO_CONFIANCA_DECLARADA * confianca_declarada
        + _PESO_SIMILARIDADE * similaridade
    )
    return bruta / _MAXIMO
