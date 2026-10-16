from classificacao.aplicacao.classificar_questao import Papeis, classificar_questao
from classificacao.dominio.arvore import Arvore, No
from classificacao.dominio.questao import Questao
from tests.unit.fakes import (
    CacheEmMemoria,
    FilaDeFalhasEmMemoria,
    ModeloFake,
    em_sequencia,
    falha_sempre,
    malformada,
    sempre,
)

QUESTAO = Questao(
    id="Q0001",
    enunciado="Sobre o desaforamento no Tribunal do Júri, analise as assertivas.",
    comando="Estão corretas as assertivas",
    alternativas={"A": "I e II", "B": "II e III"},
    disciplina_origem="Processo Penal",
    assunto_origem="Procedimento do Júri",
)
# Processo Penal (2) > Júri (10) > Desaforamento (100)
#                   > Inquérito Policial (11)
ARVORE = Arvore(
    [
        No(id=2, pai_id=None, nivel=0, caminho="Processo Penal"),
        No(id=10, pai_id=2, nivel=1, caminho="Processo Penal > Júri"),
        No(id=100, pai_id=10, nivel=2, caminho="Processo Penal > Júri > Desaforamento"),
        No(id=11, pai_id=2, nivel=1, caminho="Processo Penal > Inquérito Policial"),
    ]
)


def classificar(classificador, verificador, juiz, fila=None, cache=None):
    return classificar_questao(
        QUESTAO,
        ARVORE,
        Papeis(classificador=classificador, verificador=verificador, juiz=juiz),
        fila_de_falhas=fila or FilaDeFalhasEmMemoria(),
        cache=cache or CacheEmMemoria(),
        esperar=lambda tentativa: None,
    )


def test_com_concordancia_o_juiz_nao_e_chamado():
    juiz = ModeloFake("juiz", sempre(11))
    resultado = classificar(ModeloFake("c", sempre(10)), ModeloFake("v", sempre(10)), juiz)
    assert resultado.classificador.no_id == 10
    assert resultado.verificador.no_id == 10
    assert resultado.juiz is None
    assert juiz.chamadas == []


def test_no_desacordo_o_juiz_ve_as_duas_propostas_e_seu_voto_e_registrado():
    juiz = ModeloFake("juiz", sempre(11))
    resultado = classificar(ModeloFake("c", sempre(10)), ModeloFake("v", sempre(11)), juiz)
    assert resultado.juiz.no_id == 11
    [(_, prompt_do_juiz)] = juiz.chamadas
    assert "escolhi 10" in prompt_do_juiz
    assert "escolhi 11" in prompt_do_juiz


def test_so_o_classificador_ve_a_origem_e_os_dois_veem_a_arvore():
    classificador = ModeloFake("c", sempre(10))
    verificador = ModeloFake("v", sempre(10))
    classificar(classificador, verificador, ModeloFake("j", sempre(10)))
    [(_, prompt_classificador)] = classificador.chamadas
    [(_, prompt_verificador)] = verificador.chamadas
    assert "Procedimento do Júri" in prompt_classificador
    assert "Procedimento do Júri" not in prompt_verificador
    for prompt in (prompt_classificador, prompt_verificador):
        assert "Processo Penal > Júri > Desaforamento" in prompt


def test_resposta_malformada_ou_falha_passageira_e_tentada_de_novo():
    classificador = ModeloFake("c", em_sequencia(malformada, falha_sempre, sempre(10)))
    resultado = classificar(classificador, ModeloFake("v", sempre(10)), ModeloFake("j", sempre(10)))
    assert resultado.classificador.no_id == 10
    assert len(classificador.chamadas) == 3


def test_provedor_que_falha_sempre_vai_para_a_dlq_e_o_voto_fica_ausente():
    fila = FilaDeFalhasEmMemoria()
    juiz = ModeloFake("j", sempre(10))
    resultado = classificar(
        ModeloFake("c", sempre(10)), ModeloFake("v", falha_sempre), juiz, fila=fila
    )
    assert resultado.verificador is None
    assert resultado.classificador.no_id == 10
    assert [(q, papel) for q, papel, _ in fila.falhas] == [("Q0001", "verificador")]
    assert juiz.chamadas == []


def test_quando_os_dois_dizem_que_nenhum_no_serve_o_juiz_nao_e_chamado():
    juiz = ModeloFake("j", sempre(10))
    classificar(ModeloFake("c", sempre(None)), ModeloFake("v", sempre(None)), juiz)
    assert juiz.chamadas == []


def test_cache_evita_chamar_de_novo_o_mesmo_modelo_com_o_mesmo_prompt():
    cache = CacheEmMemoria()
    classificador = ModeloFake("api:sonnet", sempre(10))
    verificador = ModeloFake("api:gemini", sempre(10))
    juiz = ModeloFake("api:deepseek", sempre(10))
    primeira = classificar(classificador, verificador, juiz, cache=cache)
    segunda = classificar(classificador, verificador, juiz, cache=cache)
    assert segunda == primeira
    assert len(classificador.chamadas) == 1
    assert len(verificador.chamadas) == 1


def test_trocar_o_modelo_nao_reaproveita_o_cache_do_anterior():
    cache = CacheEmMemoria()
    verificador = ModeloFake("api:gemini", sempre(10))
    juiz = ModeloFake("j", sempre(10))
    classificar(ModeloFake("claude-code:sonnet", sempre(10)), verificador, juiz, cache=cache)
    novo_classificador = ModeloFake("api:sonnet", sempre(10))
    classificar(novo_classificador, verificador, juiz, cache=cache)
    assert len(novo_classificador.chamadas) == 1
