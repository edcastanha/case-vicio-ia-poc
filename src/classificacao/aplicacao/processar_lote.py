import time
from collections.abc import Callable, Sequence

from classificacao.aplicacao.classificar_questao import Papeis, classificar_questao
from classificacao.aplicacao.portas import Cache, FilaDeFalhas, RegistroDeClassificacoes
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.questao import Questao


def processar_lote(
    questoes: Sequence[Questao],
    arvore: Arvore,
    papeis: Papeis,
    registro: RegistroDeClassificacoes,
    fila_de_falhas: FilaDeFalhas,
    cache: Cache,
    esperar: Callable[[int], None] = lambda tentativa: time.sleep(2**tentativa),
) -> None:
    for questao in questoes:
        if registro.ja_classificada(questao.id):
            continue
        try:
            classificacao = classificar_questao(
                questao, arvore, papeis, fila_de_falhas, cache, esperar=esperar
            )
        except Exception as erro:  # noqa: BLE001 - uma questão nunca derruba o lote
            fila_de_falhas.registrar(questao.id, "lote", repr(erro))
            continue
        registro.salvar(classificacao)
