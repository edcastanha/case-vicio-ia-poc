"""A Origem (disciplina e assunto do site de onde a Questão veio) traduzida para um Nó."""

import re

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.v2.dominio.leis import normalizar

# Nomes do site de origem → raiz da Árvore de temas; as demais disciplinas ficam fora do recorte.
_DISCIPLINAS = {
    "direito penal": "penal",
    "penal": "penal",
    "processo penal": "processo penal",
    "direito processual penal": "processo penal",
    "direito penal - legislacao especial": "direito penal - legislacao especial",
    "criminologia": "criminologia",
}
_PARTE = re.compile(r"\s*\(parte \d+\)\s*$")


def disciplina_da_origem(disciplina: str) -> str | None:
    return _DISCIPLINAS.get(normalizar(disciplina).strip())


def no_da_origem(arvore: Arvore, disciplina: str, assunto: str) -> int | None:
    """O Nó cujo título é o assunto de origem; se há homônimos, o da disciplina de origem."""
    alvo = _PARTE.sub("", normalizar(assunto)).strip()
    if not alvo:
        return None
    mesmos = [
        no
        for no in arvore.nos_que_podem_receber_questao()
        if _PARTE.sub("", normalizar(no.titulo)).strip() == alvo
    ]
    if len(mesmos) > 1:
        raiz = disciplina_da_origem(disciplina)
        mesmos = [no for no in mesmos if normalizar(no.caminho).split(" > ")[0] == raiz]
    if len(mesmos) > 1:
        mesmos = [no for no in mesmos if not _PARTE.search(normalizar(no.titulo))]
    return mesmos[0].id if len(mesmos) == 1 else None
