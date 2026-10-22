from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore
from classificacao.v2.adaptadores.dicionarios import ler_temas_enriquecidos
from classificacao.v2.aplicacao.enriquecer_temas import rotulo_do_prompt

RAIZ = Path(__file__).parents[3]
TEMAS = ler_temas_enriquecidos(RAIZ / "dados/v2/temas_enriquecidos.jsonl")
ARVORE = ler_arvore(RAIZ / "anexos/v2/anexos-case-ia.zip")


def test_todo_no_que_pode_receber_questao_tem_tema_enriquecido_e_nenhum_a_mais():
    assert set(TEMAS) == {no.id for no in ARVORE.nos_que_podem_receber_questao()}


def test_todo_tema_veio_da_versao_publicada_do_prompt():
    texto = (RAIZ / "prompts/v2/enriquecedor/v1.md").read_text()
    assert {tema.prompt for tema in TEMAS.values()} == {rotulo_do_prompt(texto, "v1")}


def test_todo_tema_tem_descricao_e_ao_menos_cinco_termos():
    assert all(tema.descricao and len(tema.termos) >= 5 for tema in TEMAS.values())
