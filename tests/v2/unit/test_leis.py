import pytest

from classificacao.v2.dominio.leis import Lei, leis_citadas

MARIA_DA_PENHA = Lei("11340", "Lei Maria da Penha", ("maria da penha",), (4704, 6724))
DROGAS = Lei("11343", "Lei de Drogas", ("lei de drogas", "lei antidrogas"), (4708,))
CPP = Lei("3689", "Código de Processo Penal", ("codigo de processo penal", "cpp"), ())
LEIS = (MARIA_DA_PENHA, DROGAS, CPP)


@pytest.mark.parametrize(
    "texto",
    [
        "nos termos da Lei nº 11.340/2006",
        "conforme a Lei 11340/06",
        "a Lei n. 11.340, de 7 de agosto de 2006",
        "segundo a lei federal nº 11.340",
    ],
)
def test_reconhece_a_lei_pelo_numero_em_varias_grafias(texto):
    assert leis_citadas(texto, LEIS) == ("11340",)


def test_reconhece_a_lei_pelo_apelido_sem_acento_nem_caixa():
    assert leis_citadas("A LEI ANTIDROGAS e o Código de Processo Penal", LEIS) == (
        "11343",
        "3689",
    )


def test_apelido_so_conta_como_palavra_inteira():
    assert leis_citadas("o recpp da questão", LEIS) == ()


def test_numero_de_lei_fora_do_dicionario_tambem_e_extraido():
    assert leis_citadas("a Lei nº 9.296/1996 e a Lei 11.343", LEIS) == ("11343", "9296")


def test_artigo_solto_nao_e_lei():
    assert leis_citadas("art. 121 do CP, §2º, inciso 1.234", LEIS) == ()
