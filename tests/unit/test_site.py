from classificacao.dominio.questao import Questao
from classificacao.entrada.site import (
    bloco_da_previsao,
    corrigir_links,
    pagina_de_resultados,
)
from tests.unit.test_decisao import ARVORE
from tests.unit.test_gerar_entrega import classificacao

REPOSITORIO = "https://github.com/dono/repo"
PAGINAS = {"GLOSSARY.md": "glossario.md", "README.md": "como-rodar.md"}


def questao(id: str, enunciado: str = "Enunciado") -> Questao:
    return Questao(id, enunciado, "Comando", {"A": "um"}, "Penal", "Origem")


def test_link_para_arquivo_que_vira_pagina_aponta_para_a_pagina():
    texto = "Veja o [glossário](GLOSSARY.md) e o [ADR](docs/adr/0002-x.md)."
    assert corrigir_links(texto, "README.md", PAGINAS, REPOSITORIO) == (
        "Veja o [glossário](glossario.md) e o [ADR](adr/0002-x.md)."
    )


def test_link_para_arquivo_fora_do_site_aponta_para_o_github():
    texto = "[zip](anexos-case-ia.zip), [pasta](prompts/), [toml](prompts/versoes.toml)"
    assert corrigir_links(texto, "README.md", PAGINAS, REPOSITORIO) == (
        f"[zip]({REPOSITORIO}/blob/main/anexos-case-ia.zip), "
        f"[pasta]({REPOSITORIO}/tree/main/prompts/), "
        f"[toml]({REPOSITORIO}/blob/main/prompts/versoes.toml)"
    )


def test_link_relativo_e_resolvido_a_partir_da_pasta_do_arquivo():
    texto = "[rodada](rodada/resumo.csv) e [glossário](../GLOSSARY.md)"
    assert corrigir_links(texto, "dados/README.md", PAGINAS, REPOSITORIO) == (
        f"[rodada]({REPOSITORIO}/blob/main/dados/rodada/resumo.csv) e [glossário](glossario.md)"
    )


def test_links_externos_e_ancoras_ficam_como_estao():
    texto = "[uv](https://docs.astral.sh/uv/) e [seção](#como-rodar)"
    assert corrigir_links(texto, "README.md", PAGINAS, REPOSITORIO) == texto


def test_sem_entrega_a_previsao_avisa_que_ainda_nao_foi_gerada():
    assert "entrega ainda não gerada" in bloco_da_previsao(None)


def test_previsao_vira_tabela_legivel():
    previsao = (
        "precisao_prevista: 0.97\nprecisao_intervalo: 0.93-0.99\n"
        "cobertura_prevista: 0.60\ncobertura_intervalo: 0.55-0.66\n"
    )
    bloco = bloco_da_previsao(previsao)
    assert "| Precisão nas publicadas | 97% | 93% – 99% |" in bloco
    assert "| Cobertura (fração publicada) | 60% | 55% – 66% |" in bloco


def test_explicacao_da_previsao_aparece_abaixo_da_tabela_mesmo_com_dois_pontos():
    previsao = (
        "precisao_prevista: 0.97\nprecisao_intervalo: 0.93-0.99\n"
        "cobertura_prevista: 0.60\ncobertura_intervalo: 0.55-0.66\n\n"
        "Como chegamos: 34 de 34.\n"
    )
    bloco = bloco_da_previsao(previsao)
    assert bloco.index("| Precisão") < bloco.index("Como chegamos: 34 de 34.")


def resultados(entrega=None, amostra=None, enunciado="Enunciado"):
    classificacoes = {
        "Q0001": classificacao("Q0001", 100, 101),
        "Q0002": classificacao("Q0002", 100, 11, desempatador=11),
    }
    questoes = {"Q0001": questao("Q0001", enunciado), "Q0002": questao("Q0002")}
    return pagina_de_resultados(classificacoes, questoes, ARVORE, entrega, amostra or {})


def test_tabela_tem_uma_linha_por_questao_com_situacao_e_no_do_pipeline():
    pagina = resultados()
    assert "| [Q0001](#q0001) | mesmo ramo | 10 — Penal > Teoria do Crime |" in pagina
    assert "| [Q0002](#q0002) | desacordo | 11 — Penal > Teoria da Pena |" in pagina
    assert "| mesmo ramo | 1 |" in pagina  # contagem por situação


def test_sem_entrega_decisao_e_confianca_ficam_vazias_e_ha_aviso():
    pagina = resultados()
    assert "entrega ainda não gerada" in pagina
    assert "| [Q0001](#q0001) | mesmo ramo | 10 — Penal > Teoria do Crime | — | — | — |" in pagina


def test_com_entrega_mostra_decisao_confianca_e_contagem_de_decisoes():
    entrega = {
        "Q0001": {"decisao": "publicar", "confianca": "0.97"},
        "Q0002": {"decisao": "revisar", "confianca": "0.40"},
    }
    pagina = resultados(entrega=entrega)
    assert "| [Q0001](#q0001) | mesmo ramo | 10 — Penal > Teoria do Crime | publicar | 0.97 |" in (
        pagina
    )
    assert "| publicar | 1 |" in pagina
    assert "entrega ainda não gerada" not in pagina


def test_questao_da_amostra_mostra_a_resposta_e_quem_a_deu():
    pagina = resultados(amostra={"Q0001": (101, "rotulador")})
    assert "| 101 (rotulador) |" in pagina


def test_detalhe_traz_o_voto_de_cada_papel_com_a_versao_do_prompt():
    pagina = resultados()
    assert '<details id="q0002">' in pagina
    assert "Desempatador" in pagina and "Penal > Teoria da Pena" in pagina


def test_texto_da_questao_e_escapado_no_html_do_detalhe():
    pagina = resultados(enunciado="Pena <b>maior</b> & menor")
    assert "Pena &lt;b&gt;maior&lt;/b&gt; &amp; menor" in pagina
    assert "<b>maior</b>" not in pagina
