from collections.abc import Mapping

from classificacao.aplicacao.classificar_questao import Classificacao
from classificacao.aplicacao.gerar_entrega import Sinais
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.calibracao import Rotulo
from classificacao.dominio.decisao import Decisao, decidir
from classificacao.dominio.pontuacao import pontuar


def rotulos_de_calibracao(
    classificacoes: Mapping[str, Classificacao],
    rotulos: Mapping[str, int | None],
    arvore: Arvore,
    sinais: Mapping[str, Sinais],
) -> list[Rotulo]:
    """Pares (pontuação, acertou?) das Questões rotuladas que seriam publicadas com limiar zero.

    A Régua só mede publicadas; desacordos, Temas duplicados e modelos em dúvida nunca publicam,
    então não entram na calibração (seus rótulos servem ao diagnóstico).
    """
    pares = []
    for questao_id, gabarito in sorted(rotulos.items()):
        c = classificacoes.get(questao_id)
        if c is None or c.classificador is None or c.verificador is None:
            continue
        classificador, verificador = c.classificador.voto(), c.verificador.voto()
        similaridade = sinais.get(questao_id, Sinais()).similaridade
        pontuacao = pontuar(arvore, classificador, verificador, similaridade)
        resultado = decidir(arvore, classificador, verificador, None, pontuacao, limiar=0.0)
        if resultado.decisao is not Decisao.PUBLICAR:
            continue
        acertou = gabarito is not None and arvore.mesmo_ramo(resultado.tema_central_id, gabarito)
        pares.append(Rotulo(pontuacao, acertou))
    return pares
