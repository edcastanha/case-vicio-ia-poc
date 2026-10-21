import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.questao import Questao
from classificacao.v1.aplicacao.classificar_questao import Papeis, classificar_questao
from classificacao.v1.aplicacao.portas import Cache, FilaDeFalhas, RegistroDeClassificacoes
from classificacao.v1.aplicacao.prompts import PromptsDosPapeis


def processar_lote(
    questoes: Sequence[Questao],
    arvore: Arvore,
    papeis: Papeis,
    prompts: PromptsDosPapeis,
    registro: RegistroDeClassificacoes,
    fila_de_falhas: FilaDeFalhas,
    cache: Cache,
    esperar: Callable[[int], None] = lambda tentativa: time.sleep(2**tentativa),
    paralelismo: int = 1,
) -> None:
    trava = threading.Lock()

    def processar(questao: Questao) -> None:
        try:
            classificacao = classificar_questao(
                questao, arvore, papeis, prompts, fila_de_falhas, cache, esperar=esperar
            )
        except Exception as erro:  # noqa: BLE001 - uma questão nunca derruba o lote
            with trava:
                fila_de_falhas.registrar(questao.id, "lote", repr(erro))
            return
        with trava:
            registro.salvar(classificacao)

    pendentes = [q for q in questoes if not registro.ja_classificada(q.id)]
    with ThreadPoolExecutor(max_workers=paralelismo) as executor:
        list(executor.map(processar, pendentes))
