from classificacao.nucleo.dominio.arvore import Arvore, No

# Penal (1) > Teoria do Crime (10) > Ilicitude (100), Culpabilidade (101)
#           > Teoria da Pena (11)
PENAL = No(id=1, pai_id=None, nivel=0, caminho="Penal")
TEORIA_DO_CRIME = No(id=10, pai_id=1, nivel=1, caminho="Penal > Teoria do Crime")
ILICITUDE = No(id=100, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Ilicitude")
CULPABILIDADE = No(id=101, pai_id=10, nivel=2, caminho="Penal > Teoria do Crime > Culpabilidade")
TEORIA_DA_PENA = No(id=11, pai_id=1, nivel=1, caminho="Penal > Teoria da Pena")


def arvore() -> Arvore:
    return Arvore([PENAL, TEORIA_DO_CRIME, ILICITUDE, CULPABILIDADE, TEORIA_DA_PENA])


def test_subtema_esta_no_mesmo_ramo_do_tema_pai_nos_dois_sentidos():
    assert arvore().mesmo_ramo(100, 10)
    assert arvore().mesmo_ramo(10, 100)


def test_subtemas_irmaos_nao_estao_no_mesmo_ramo():
    assert not arvore().mesmo_ramo(100, 101)


def test_o_proprio_no_esta_no_mesmo_ramo():
    assert arvore().mesmo_ramo(100, 100)


def test_disciplina_nao_esta_no_mesmo_ramo_do_subtema_neto():
    assert not arvore().mesmo_ramo(1, 100)


def test_questao_pode_ir_para_tema_ou_subtema_ativo():
    assert arvore().pode_receber_questao(10)
    assert arvore().pode_receber_questao(100)


def test_questao_nao_pode_ir_para_disciplina():
    assert not arvore().pode_receber_questao(1)


def test_questao_nao_pode_ir_para_no_inativo():
    inativo = No(id=12, pai_id=1, nivel=1, caminho="Penal > Antigo", ativo=False)
    assert not Arvore([PENAL, inativo]).pode_receber_questao(12)


def test_questao_nao_pode_ir_para_no_inexistente():
    assert not arvore().pode_receber_questao(999)


def test_consenso_entre_mesmo_no_e_o_proprio_no():
    assert arvore().no_de_consenso(100, 100) == 100


def test_consenso_entre_tema_e_seu_subtema_e_o_tema():
    assert arvore().no_de_consenso(100, 10) == 10
    assert arvore().no_de_consenso(10, 100) == 10


def test_consenso_entre_subtemas_irmaos_e_o_tema_pai():
    assert arvore().no_de_consenso(100, 101) == 10


def test_nao_ha_consenso_entre_temas_diferentes():
    assert arvore().no_de_consenso(10, 11) is None


def test_nao_ha_consenso_entre_subtema_e_tema_de_outro_ramo():
    assert arvore().no_de_consenso(100, 11) is None


def test_voto_em_no_inexistente_nao_gera_ramo_nem_consenso():
    assert not arvore().mesmo_ramo(999, 10)
    assert arvore().no_de_consenso(999, 10) is None


def arvore_com_duplicado() -> Arvore:
    # Penal (1) > Lavagem de Dinheiro (12) > Delação (120)
    # Leg. Especial (2) > Lavagem de Dinheiro (21)
    return Arvore(
        [
            PENAL,
            TEORIA_DO_CRIME,
            ILICITUDE,
            No(id=12, pai_id=1, nivel=1, caminho="Penal > Lavagem de Dinheiro"),
            No(id=120, pai_id=12, nivel=2, caminho="Penal > Lavagem de Dinheiro > Delação"),
            No(id=2, pai_id=None, nivel=0, caminho="Leg. Especial"),
            No(id=21, pai_id=2, nivel=1, caminho="Leg. Especial > Lavagem de dinheiro"),
        ]
    )


def test_tema_com_mesmo_titulo_em_outra_disciplina_e_duplicado_assim_como_seus_subtemas():
    arvore = arvore_com_duplicado()
    assert arvore.em_tema_duplicado(12)
    assert arvore.em_tema_duplicado(21)
    assert arvore.em_tema_duplicado(120)


def test_tema_sem_par_em_outra_disciplina_nao_e_duplicado():
    arvore = arvore_com_duplicado()
    assert not arvore.em_tema_duplicado(10)
    assert not arvore.em_tema_duplicado(100)
