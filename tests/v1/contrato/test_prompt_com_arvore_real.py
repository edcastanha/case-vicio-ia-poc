from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore
from classificacao.v1.aplicacao.prompts import arvore_para_prompt

ZIP = Path(__file__).parents[3] / "anexos/v1/anexos-case-ia.zip"


def test_arvore_no_prompt_nao_leva_as_contagens_de_questoes_do_source():
    texto = arvore_para_prompt(ler_arvore(ZIP))
    assert "[4366] Criminologia > Classificação das Vítimas" in texto
    assert "questões" not in texto
