from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.nucleo.dominio.questao import Questao
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.aplicacao.montar_sinais import CandidatoComSinais
from classificacao.v2.aplicacao.validacao_cruzada import validar
from classificacao.v2.dominio.candidatos import Sinais

ARVORE = Arvore(
    [
        No(1, None, 0, "Penal"),
        No(10, 1, 1, "Penal > A", titulo="A"),
        No(11, 1, 1, "Penal > B", titulo="B"),
    ]
)


def sinais(similaridade):
    return Sinais(similaridade, 1, 0.0, 0.0, 0.0, 0.0, 0.0, 1)


def test_nenhuma_questao_do_fold_de_teste_e_vista_como_rotulada_e_todas_sao_previstas_uma_vez():
    folha = {f"Q{i:02}": Gabarito(10 if i % 2 else 11) for i in range(20)}
    questoes = {i: Questao(i, "", "", {}, "", "") for i in folha}
    vistas = []

    def montar(lote, rotuladas):
        vistas.append(({q.id for q in lote}, set(rotuladas)))
        # o Gabarito sempre aparece com similaridade maior: a similaridade pura acerta tudo
        return {
            q.id: [
                CandidatoComSinais(10, sinais(0.9 if folha[q.id].tema_central_id == 10 else 0.1)),
                CandidatoComSinais(11, sinais(0.9 if folha[q.id].tema_central_id == 11 else 0.1)),
            ]
            for q in lote
        }

    resultado = validar("similaridade", ARVORE, questoes, folha, montar, alvo=0.9, folds=5)
    testes = [lote for lote, rotuladas in vistas[1::2]]
    assert all(not (lote & rotuladas) for lote, rotuladas in vistas[1::2])
    assert sorted(i for lote in testes for i in lote) == sorted(folha)
    assert sorted(p.questao_id for p in resultado.previsoes) == sorted(folha)
    assert resultado.acertos == resultado.publicadas == 20
    assert resultado.cobertura == 1.0


def test_ranqueador_ramo_pontua_pela_massa_do_ramo_e_publica_no_pai_na_duvida_entre_irmaos():
    from classificacao.v2.aplicacao.ranqueador import Ranqueador

    arvore = Arvore(
        [
            No(1, None, 0, "Penal"),
            No(10, 1, 1, "Penal > A", titulo="A"),
            No(100, 10, 2, "Penal > A > x", titulo="x"),
            No(101, 10, 2, "Penal > A > y", titulo="y"),
        ]
    )
    folha = {f"Q{i}": Gabarito(100 if i % 2 else 101) for i in range(20)}
    # Os dois Subtemas parecem igualmente prováveis; o pai, de similaridade baixa, nunca é Gabarito.
    candidatos = [
        CandidatoComSinais(10, sinais(0.1)),
        CandidatoComSinais(100, sinais(0.8)),
        CandidatoComSinais(101, sinais(0.8)),
    ]
    ranqueador = Ranqueador("ramo").treinar(arvore, {q: candidatos for q in folha}, folha)
    escolha = ranqueador.escolher(arvore, candidatos)
    assert escolha.no_id == 10
    assert escolha.pontuacao > 0.9
