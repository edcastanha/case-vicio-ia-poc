import pytest

from classificacao.v2.dominio.temas import TemaEnriquecido, corrigir

ORIGINAL = TemaEnriquecido(
    no_id=7,
    descricao="Descrição antiga.",
    nao_entra="Vai para Penal > Outro.",
    termos=("a", "b"),
    leis=("CP, art. 1º",),
    prompt="enriquecedor/v1@abc",
)


def test_a_correcao_troca_so_os_campos_revisados_e_guarda_o_rotulo_do_enriquecimento():
    temas = corrigir({7: ORIGINAL}, {7: {"descricao": "Nova.", "termos": ["c"]}})

    assert temas[7].descricao == "Nova."
    assert temas[7].termos == ("c",)
    assert temas[7].nao_entra == ORIGINAL.nao_entra
    assert temas[7].leis == ORIGINAL.leis
    assert temas[7].prompt == ORIGINAL.prompt


def test_sem_correcao_o_tema_fica_como_o_enriquecimento_gerou():
    assert corrigir({7: ORIGINAL}, {}) == {7: ORIGINAL}


def test_correcao_de_no_sem_tema_enriquecido_e_erro():
    with pytest.raises(ValueError, match="99"):
        corrigir({7: ORIGINAL}, {99: {"descricao": "x"}})


def test_correcao_de_campo_que_nao_e_texto_do_tema_e_erro():
    with pytest.raises(ValueError, match="prompt"):
        corrigir({7: ORIGINAL}, {7: {"prompt": "outro"}})
