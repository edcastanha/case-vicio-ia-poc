from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.v1.dominio.decisao import Voto
from classificacao.v1.dominio.pontuacao import pontuar

# Penal (1) > Teoria do Crime (10) > Ilicitude (100), Culpabilidade (101)
#           > Teoria da Pena (11)
ARVORE = Arvore(
    [
        No(id=1, pai_id=None, nivel=0, caminho="Penal"),
        No(id=10, pai_id=1, nivel=1, caminho="Penal > Teoria do Crime"),
        No(id=100, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Ilicitude"),
        No(id=101, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Culpabilidade"),
        No(id=11, pai_id=1, nivel=1, caminho="Penal > Teoria da Pena"),
    ]
)


def test_concordancia_no_mesmo_no_pontua_acima_de_concordancia_so_de_ramo():
    mesmo_no = pontuar(ARVORE, Voto(100, 0.8), Voto(100, 0.8), similaridade=0.5)
    so_ramo = pontuar(ARVORE, Voto(100, 0.8), Voto(101, 0.8), similaridade=0.5)
    assert mesmo_no > so_ramo


def test_desacordo_confiante_pontua_abaixo_de_concordancia_de_ramo_hesitante():
    desacordo = pontuar(ARVORE, Voto(100, 1.0), Voto(11, 1.0), similaridade=1.0)
    ramo = pontuar(ARVORE, Voto(100, 0.0), Voto(101, 0.0), similaridade=0.0)
    assert desacordo < ramo


def test_mesmo_voto_em_no_nao_publicavel_nao_conta_como_concordancia():
    ramo = pontuar(ARVORE, Voto(100, 0.0), Voto(101, 0.0), similaridade=0.0)
    assert pontuar(ARVORE, Voto(1, 1.0), Voto(1, 1.0), similaridade=1.0) < ramo
    assert pontuar(ARVORE, Voto(999, 1.0), Voto(999, 1.0), similaridade=1.0) < ramo


def test_pontuacao_vai_de_zero_no_pior_caso_a_um_no_melhor():
    assert pontuar(ARVORE, Voto(100, 1.0), Voto(100, 1.0), similaridade=1.0) == 1.0
    assert pontuar(ARVORE, Voto(100, 0.0), Voto(11, 0.0), similaridade=0.0) == 0.0
