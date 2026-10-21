from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.questao import Questao
from classificacao.v1.aplicacao.amostra_cega import gerar_amostra_cega
from classificacao.v1.aplicacao.classificar_questao import Classificacao, Proposta

# Penal (1) > Teoria do Crime (10) > Ilicitude (100), Culpabilidade (101), Tipicidade (102)
#           > Teoria da Pena (11) > Dosimetria (110)
ARVORE = Arvore(
    [
        No(id=1, pai_id=None, nivel=0, caminho="Penal"),
        No(id=10, pai_id=1, nivel=1, caminho="Penal > Teoria do Crime"),
        No(id=100, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Ilicitude"),
        No(id=101, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Culpabilidade"),
        No(id=102, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Tipicidade"),
        No(id=11, pai_id=1, nivel=1, caminho="Penal > Teoria da Pena"),
        No(id=110, pai_id=11, nivel=2, caminho="Penal > Teoria da Pena > Dosimetria"),
    ]
)


def questao(id: str) -> Questao:
    return Questao(id, f"enunciado {id}", "comando", {"A": "a"}, "Penal", "")


def concordante(id: str, no_id: int = 100) -> Classificacao:
    return Classificacao(id, Proposta(no_id, 0.9, "c"), Proposta(no_id, 0.9, "v"), None)


def em_desacordo(id: str) -> Classificacao:
    return Classificacao(
        id, Proposta(100, 0.9, "c"), Proposta(110, 0.9, "v"), Proposta(110, 0.6, "j")
    )


def gerar(classificacoes, n, semente=7):
    questoes = {c.questao_id: questao(c.questao_id) for c in classificacoes}
    return gerar_amostra_cega(classificacoes, questoes, ARVORE, n=n, semente=semente)


def test_amostra_tem_o_tamanho_pedido_ids_unicos_e_e_reprodutivel():
    classificacoes = [concordante(f"Q{i:04d}") for i in range(40)]
    amostra = gerar(classificacoes, n=10)
    assert len(amostra) == 10
    assert len({item.questao.id for item in amostra}) == 10
    assert [i.questao.id for i in gerar(classificacoes, n=10)] == [i.questao.id for i in amostra]


def test_candidatos_incluem_os_nos_votados_e_distratores_publicaveis():
    [item] = gerar([em_desacordo("Q0001")], n=1)
    assert {100, 110} <= set(item.candidatos)
    assert len(item.candidatos) >= 4
    assert len(set(item.candidatos)) == len(item.candidatos)
    assert all(ARVORE.pode_receber_questao(no) for no in item.candidatos)


def test_concordancia_no_mesmo_no_tambem_recebe_distratores():
    [item] = gerar([concordante("Q0001")], n=1)
    assert 100 in item.candidatos
    assert len(item.candidatos) >= 4


def test_posicao_do_no_votado_varia_para_nao_denunciar_os_modelos():
    classificacoes = [concordante(f"Q{i:04d}") for i in range(30)]
    posicoes = {item.candidatos.index(100) for item in gerar(classificacoes, n=30)}
    assert len(posicoes) > 1


def test_oitenta_por_cento_da_amostra_vem_das_questoes_com_concordancia():
    concordantes = [concordante(f"Q{i:04d}") for i in range(50)]
    desacordos = [em_desacordo(f"Q{i:04d}") for i in range(50, 100)]
    amostra = gerar(concordantes + desacordos, n=20)
    ids_concordantes = {c.questao_id for c in concordantes}
    assert sum(item.questao.id in ids_concordantes for item in amostra) == 16


def test_voto_em_tema_duplicado_traz_o_homonimo_da_outra_disciplina_como_candidato():
    arvore = Arvore(
        [
            No(id=1, pai_id=None, nivel=0, caminho="Penal"),
            No(id=12, pai_id=1, nivel=1, caminho="Penal > Lavagem de Dinheiro"),
            No(id=13, pai_id=1, nivel=1, caminho="Penal > Furto"),
            No(id=14, pai_id=1, nivel=1, caminho="Penal > Roubo"),
            No(id=15, pai_id=1, nivel=1, caminho="Penal > Estelionato"),
            No(id=16, pai_id=1, nivel=1, caminho="Penal > Dano"),
            No(id=2, pai_id=None, nivel=0, caminho="Leg. Especial"),
            No(id=21, pai_id=2, nivel=1, caminho="Leg. Especial > Lavagem de Dinheiro"),
        ]
    )
    classificacao = Classificacao("Q0001", Proposta(12, 0.9, "c"), Proposta(12, 0.9, "v"), None)
    [item] = gerar_amostra_cega(
        [classificacao], {"Q0001": questao("Q0001")}, arvore, n=1, semente=7
    )
    assert {12, 21} <= set(item.candidatos)
