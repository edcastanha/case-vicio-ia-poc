from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.questao import Questao
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.aplicacao.gerar_entrega import gerar_entrega, texto_da_previsao
from classificacao.v2.aplicacao.montar_sinais import CandidatoComSinais
from classificacao.v2.dominio.candidatos import Sinais

ARVORE = Arvore(
    [
        No(1, None, 0, "Penal"),
        No(10, 1, 1, "Penal > A", titulo="A"),
        No(11, 1, 1, "Penal > B", titulo="B"),
    ]
)
# Q00–Q39 na Folha-verdade (antigas); Q400–Q409 avaliadas, uma delas militar.
FOLHA = {f"Q{i:04}": Gabarito(10 if i % 2 else 11) for i in range(40)}
AVALIADAS = [f"Q{400 + i}" for i in range(10)]
QUESTOES = [Questao(i, "", "", {}, "Direito Penal", "") for i in [*FOLHA, *AVALIADAS]]
QUESTOES[-1] = Questao(AVALIADAS[-1], "", "", {}, "Direito Penal Militar", "")


def montar(lote, rotuladas):
    def alvo(questao_id):
        return FOLHA[questao_id].tema_central_id if questao_id in FOLHA else 10

    return {
        q.id: [
            CandidatoComSinais(
                no, Sinais(0.9 if alvo(q.id) == no else 0.2, 1, 0.0, 0.0, 0.0, 0.0, 0.0, 1)
            )
            for no in (10, 11)
        ]
        for q in lote
    }


def test_entrega_tem_todas_as_questoes_publica_acima_do_limiar_e_preve_fora_da_folha():
    entrega = gerar_entrega(QUESTOES, ARVORE, FOLHA, montar, "similaridade", 0.9, repeticoes=50)
    por_id = {linha["id"]: linha for linha in entrega.linhas}
    assert len(por_id) == 50
    assert por_id["Q400"]["decisao"] == "publicar" and por_id["Q400"]["tema_central_id"] == "10"
    assert por_id[AVALIADAS[-1]]["decisao"] == "fora"
    p = entrega.previsao
    assert p.avaliadas == 10 and p.publicadas == 9
    assert p.cobertura == 0.9
    assert p.precisao == (40 + 1) / (40 + 2)
    texto = texto_da_previsao(p, "similaridade", "fake")
    assert texto.splitlines()[0] == "precisao_prevista: 0.98"
    assert texto.splitlines()[2] == "cobertura_prevista: 0.90"
