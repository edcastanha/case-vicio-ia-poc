from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore
from classificacao.v2.adaptadores.dicionarios import ler_leis
from classificacao.v2.dominio.leis import normalizar

RAIZ = Path(__file__).parents[3]
LEIS = ler_leis(RAIZ / "dados/v2/leis.csv")
ARVORE = ler_arvore(RAIZ / "anexos/v2/anexos-case-ia.zip")


def test_todo_no_do_dicionario_de_leis_existe_e_pode_receber_questao():
    assert all(ARVORE.pode_receber_questao(no) for lei in LEIS for no in lei.nos)


def test_apelidos_ja_estao_normalizados_e_numeros_nao_se_repetem():
    assert all(apelido == normalizar(apelido) for lei in LEIS for apelido in lei.apelidos)
    assert len({lei.numero for lei in LEIS}) == len(LEIS)
