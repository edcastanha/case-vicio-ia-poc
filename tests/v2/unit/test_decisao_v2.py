from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.decisao import Decisao
from classificacao.v2.dominio.decisao import Pontuado, decidir, extras

# Penal (1) > Teoria da Pena (10) > Pena de Multa (100); > Prescrição (11)
# Leg. Especial (2) > LEP (20); Processo Penal (3) > LEP (30)  ← Tema duplicado
ARVORE = Arvore(
    [
        No(1, None, 0, "Penal", titulo="Penal"),
        No(10, 1, 1, "Penal > Teoria da Pena", titulo="Teoria da Pena"),
        No(100, 10, 2, "Penal > Teoria da Pena > Pena de Multa", titulo="Pena de Multa"),
        No(11, 1, 1, "Penal > Prescrição", titulo="Prescrição"),
        No(2, None, 0, "Leg. Especial", titulo="Leg. Especial"),
        No(20, 2, 1, "Leg. Especial > LEP", titulo="LEP"),
        No(3, None, 0, "Processo Penal", titulo="Processo Penal"),
        No(30, 3, 1, "Processo Penal > LEP", titulo="LEP"),
    ]
)


def test_publica_o_escolhido_quando_a_pontuacao_alcanca_o_limiar():
    r = decidir(ARVORE, Pontuado(10, 0.9, voto_das_vizinhas=0.0), 0.8, "Direito Penal")
    assert (r.decisao, r.tema_central_id, r.motivo) == (Decisao.PUBLICAR, 10, "")


def test_abaixo_do_limiar_vai_para_revisar_com_a_sugestao_e_o_motivo():
    r = decidir(ARVORE, Pontuado(100, 0.5, 0.0), 0.8, "Direito Penal")
    assert (r.decisao, r.tema_central_id) == (Decisao.REVISAR, 100)
    assert r.motivo == "pontuação 0.50 abaixo do limiar 0.80"


def test_tema_duplicado_so_publica_com_exemplo_da_equipe_entre_as_vizinhas():
    sem_exemplo = decidir(ARVORE, Pontuado(20, 0.99, 0.0), 0.8, "Direito Penal")
    assert (sem_exemplo.decisao, sem_exemplo.motivo) == (
        Decisao.REVISAR,
        "tema duplicado sem exemplo da equipe entre as vizinhas",
    )
    assert (
        decidir(ARVORE, Pontuado(20, 0.99, 0.6), 0.8, "Direito Penal").decisao is Decisao.PUBLICAR
    )


def test_disciplina_militar_vai_para_fora_mesmo_com_pontuacao_alta():
    r = decidir(ARVORE, Pontuado(10, 0.99, 0.0), 0.8, "Direito Penal Militar")
    assert (r.decisao, r.tema_central_id) == (Decisao.FORA, None)
    assert r.motivo == "disciplina de origem fora da árvore (Direito Penal Militar)"


def test_outra_disciplina_de_origem_nao_e_sinal_de_fora():
    # Q0016 vem como Direito Constitucional e é sobre prisão: a Origem engana.
    assert decidir(ARVORE, Pontuado(10, 0.99, 0.0), 0.8, "Direito Constitucional").decisao is (
        Decisao.PUBLICAR
    )


def test_sem_limiar_calibrado_nada_e_publicado():
    assert (
        decidir(ARVORE, Pontuado(10, 0.99, 0.0), None, "Direito Penal").decisao is Decisao.REVISAR
    )


def test_extras_sao_outros_ramos_acima_do_limiar_de_extra_no_maximo_dois():
    candidatos = [
        Pontuado(10, 0.9, 0),
        Pontuado(100, 0.8, 0),
        Pontuado(11, 0.7, 0),
        Pontuado(20, 0.6, 0),
        Pontuado(30, 0.2, 0),
    ]
    assert extras(ARVORE, 10, candidatos, limiar=0.5) == (11, 20)
