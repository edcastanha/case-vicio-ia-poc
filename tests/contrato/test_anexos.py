from pathlib import Path

import pytest

from classificacao.adaptadores.anexos import ler_arvore, ler_questoes, limpar_html

ZIP = Path(__file__).parents[2] / "anexos-case-ia.zip"
Q0016_HTML = (
    'sobre o tema\n<span style="font-style: italic;">prisão</span>, '
    "avalie as assertivas a seguir.\n  <br>  <br>  I. Consoante a jurisprudência"
)


@pytest.mark.parametrize(
    "html, texto",
    [
        # Q0009, alternativa
        (
            "crime de furto qualificado pelo rompimento  de obstáculo à subtração da coisa.  <br> ",
            "crime de furto qualificado pelo rompimento de obstáculo à subtração da coisa.",
        ),
        # Q0016, enunciado
        (
            Q0016_HTML,
            "sobre o tema prisão, avalie as assertivas a seguir.\nI. Consoante a jurisprudência",
        ),
        # Q0001, enunciado
        (
            "analise as assertivas abaixo.<br><br>I - O desaforamento é admitido",
            "analise as assertivas abaixo.\nI - O desaforamento é admitido",
        ),
        ("art.&nbsp;121, <b>caput</b>, do <i>CP</i>", "art. 121, caput, do CP"),
    ],
)
def test_limpeza_mantem_o_texto_e_tira_o_html(html, texto):
    assert limpar_html(html) == texto


def test_le_as_359_questoes_do_zip_sem_html():
    questoes = ler_questoes(ZIP)
    assert len(questoes) == 359
    assert len({q.id for q in questoes}) == 359
    textos = [q.enunciado for q in questoes] + [
        alternativa for q in questoes for alternativa in q.alternativas.values()
    ]
    assert not [t for t in textos if "<" in t or "&nbsp;" in t]


def test_questao_lida_preserva_comando_e_origem():
    q0001 = next(q for q in ler_questoes(ZIP) if q.id == "Q0001")
    assert q0001.comando == "Estão corretas as assertivas"
    assert q0001.disciplina_origem == "Processo Penal"
    assert q0001.assunto_origem == "Procedimento do Júri"
    assert q0001.alternativas["B"] == "II e IV, apenas."


def test_arvore_real_tem_371_nos_que_podem_receber_questao():
    arvore = ler_arvore(ZIP)
    assert len(arvore.nos_que_podem_receber_questao()) == 371
    assert not arvore.pode_receber_questao(4365)  # Criminologia (Disciplina)
    assert arvore.mesmo_ramo(4366, 4365)  # Classificação das Vítimas < Criminologia


def test_arvore_no_prompt_nao_leva_as_contagens_de_questoes_do_source():
    from classificacao.aplicacao.prompts import arvore_para_prompt

    texto = arvore_para_prompt(ler_arvore(ZIP))
    assert "[4366] Criminologia > Classificação das Vítimas" in texto
    assert "questões" not in texto


def test_arvore_real_tem_8_pares_de_temas_duplicados_entre_disciplinas():
    arvore = ler_arvore(ZIP)
    temas = [no for no in arvore.nos_que_podem_receber_questao() if no.nivel == 1]
    assert sum(arvore.em_tema_duplicado(no.id) for no in temas) == 16
