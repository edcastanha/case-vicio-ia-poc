import pytest

from classificacao.aplicacao.classificar_questao import Classificacao, Proposta
from classificacao.aplicacao.prompts import Prompt, VersoesDePromptMisturadas, exigir_versao_unica


def test_rotulo_identifica_papel_versao_e_conteudo():
    prompt = Prompt("classificador", "v1", "texto")
    assert prompt.rotulo.startswith("classificador/v1@")
    assert prompt.rotulo != Prompt("classificador", "v1", "texto alterado").rotulo


def voto(no_id: int, prompt: str) -> Proposta:
    return Proposta(no_id, 0.9, "j", prompt=prompt)


def classificacao(id: str, classificador: str, verificador: str, desempatador: str | None = None):
    return Classificacao(
        id,
        voto(10, classificador),
        voto(10, verificador),
        None if desempatador is None else voto(10, desempatador),
    )


def test_uma_versao_por_prompt_devolve_as_versoes_usadas():
    classificacoes = [
        classificacao("Q0001", "classificador/v1@a", "verificador/v1@b", "desempatador/v1@c"),
        # Desempatador sozinho usa o prompt do Verificador: não é mistura.
        classificacao("Q0002", "classificador/v1@a", "verificador/v1@b", "verificador/v1@b"),
    ]
    assert exigir_versao_unica(classificacoes) == [
        "classificador/v1@a",
        "desempatador/v1@c",
        "verificador/v1@b",
    ]


def test_duas_versoes_do_mesmo_prompt_na_rodada_sao_recusadas():
    classificacoes = [
        classificacao("Q0001", "classificador/v1@a", "verificador/v1@b"),
        classificacao("Q0002", "classificador/v2@d", "verificador/v1@b"),
    ]
    with pytest.raises(VersoesDePromptMisturadas, match="classificador/v1@a, classificador/v2@d"):
        exigir_versao_unica(classificacoes)


def test_mesma_versao_com_texto_editado_e_mistura():
    classificacoes = [
        classificacao("Q0001", "classificador/v1@a", "verificador/v1@b"),
        classificacao("Q0002", "classificador/v1@e", "verificador/v1@b"),
    ]
    with pytest.raises(VersoesDePromptMisturadas):
        exigir_versao_unica(classificacoes)


def test_voto_sem_versao_de_prompt_e_recusado():
    with pytest.raises(VersoesDePromptMisturadas, match="Q0001"):
        exigir_versao_unica([classificacao("Q0001", "", "verificador/v1@b")])
