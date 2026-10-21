"""Entrega da v2: calibra na Folha-verdade fora do fold, decide as 659 e prevê o resultado."""

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.calibracao import (
    Rotulo,
    ajustar_curva,
    intervalo_de_wilson,
    limiar_por_laplace,
    taxa_de_laplace,
)
from classificacao.nucleo.dominio.decisao import Decisao
from classificacao.nucleo.dominio.entrega import ItemDaEntrega, montar_entrega
from classificacao.nucleo.dominio.questao import Questao
from classificacao.nucleo.dominio.regua import Gabarito
from classificacao.v2.aplicacao.ranqueador import Ranqueador
from classificacao.v2.aplicacao.validacao_cruzada import Montar, validar
from classificacao.v2.aplicacao.validacao_cruzada import Resultado as Validacao
from classificacao.v2.dominio.decisao import Pontuado, decidir, extras

CONFIANCA_DE_FORA = 0.5  # nenhuma Questão militar na Folha-verdade para medir


@dataclass(frozen=True)
class Previsao:
    alvo: float
    precisao: float
    precisao_intervalo: tuple[float, float]
    cobertura: float
    cobertura_intervalo: tuple[float, float]
    validacao: Validacao
    publicadas: int
    avaliadas: int
    cobertura_antigas: float
    cobertura_novas: float


@dataclass(frozen=True)
class Entrega:
    linhas: list[dict[str, str]]
    previsao: Previsao


def gerar_entrega(
    questoes: Sequence[Questao],
    arvore: Arvore,
    folha: Mapping[str, Gabarito],
    montar: Montar,
    tipo: str,
    alvo: float,
    repeticoes: int = 1000,
    semente: int = 0,
) -> Entrega:
    por_id = {q.id: q for q in questoes}
    validacao = validar(tipo, arvore, por_id, folha, montar, alvo, semente=semente)
    rotulos = [Rotulo(p.pontuacao, p.acertou) for p in validacao.previsoes]
    curva = ajustar_curva(rotulos, faixas=5)
    sinais_da_folha = montar([por_id[i] for i in folha], folha)
    ranqueador = Ranqueador(tipo, semente).treinar(arvore, sinais_da_folha, folha)

    sinais = montar(questoes, folha)
    itens, pontuacoes = [], {}
    for questao in questoes:
        candidatos = sinais[questao.id]
        valores = ranqueador.pontuar(arvore, candidatos)
        pontuados = [
            Pontuado(c.no_id, float(v), c.sinais.voto_das_vizinhas)
            for c, v in zip(candidatos, valores, strict=True)
        ]
        escolhido = max(pontuados, key=lambda p: p.pontuacao)
        resultado = decidir(arvore, escolhido, validacao.limiar, questao.disciplina_origem)
        pontuacoes[questao.id] = escolhido.pontuacao
        itens.append(_item(arvore, questao.id, resultado, escolhido, pontuados, validacao, curva))
    linhas = montar_entrega(itens, set(por_id))
    publicadas = {i.id for i in itens if i.resultado.decisao is Decisao.PUBLICAR}
    previsao = _prever(validacao, rotulos, pontuacoes, publicadas, folha, repeticoes, semente, alvo)
    return Entrega(linhas, previsao)


def _item(arvore, questao_id, resultado, escolhido, pontuados, validacao, curva) -> ItemDaEntrega:
    if resultado.decisao is Decisao.FORA:
        return ItemDaEntrega(questao_id, resultado, (), CONFIANCA_DE_FORA)
    limiar = validacao.limiar if validacao.limiar is not None else 1.0
    extras_ids = extras(arvore, escolhido.no_id, pontuados, limiar)
    return ItemDaEntrega(questao_id, resultado, extras_ids, curva(escolhido.pontuacao))


def _prever(
    validacao: Validacao,
    rotulos: Sequence[Rotulo],
    pontuacoes: Mapping[str, float],
    publicadas: set[str],
    folha: Mapping[str, Gabarito],
    repeticoes: int,
    semente: int,
    alvo: float,
) -> Previsao:
    """Precisão: Laplace fora do fold, intervalo de Wilson unido ao bootstrap do limiar.
    Cobertura: fração publicada fora da Folha-verdade; intervalo pelos limiares do bootstrap."""
    avaliadas = [i for i in pontuacoes if i not in folha]
    cobertura = sum(i in publicadas for i in avaliadas) / len(avaliadas)
    precisao = taxa_de_laplace(validacao.acertos, validacao.publicadas)
    piso, teto = intervalo_de_wilson(validacao.acertos, max(validacao.publicadas, 1))
    sorteio = random.Random(semente)
    precisoes, coberturas = [], []
    for _ in range(repeticoes):
        indices = [sorteio.randrange(len(rotulos)) for _ in rotulos]
        limiar = limiar_por_laplace([rotulos[i] for i in indices], alvo)
        if limiar is None:
            coberturas.append(0.0)
            continue
        coberturas.append(sum(pontuacoes[i] >= limiar for i in avaliadas) / len(avaliadas))
        sorteados = set(indices)
        fora_da_reamostra = [
            r for i, r in enumerate(rotulos) if i not in sorteados and r.pontuacao >= limiar
        ]
        if fora_da_reamostra:
            precisoes.append(sum(r.acertou for r in fora_da_reamostra) / len(fora_da_reamostra))
    precisoes.sort()
    coberturas.sort()

    def percentil(valores, q):
        return valores[int(q * (len(valores) - 1))] if valores else 0.0

    precisao_intervalo = (
        min(piso, percentil(precisoes, 0.025)),
        max(teto, percentil(precisoes, 0.975)),
    )
    antigas = [i for i in avaliadas if int(i[1:]) <= 359]
    novas = [i for i in avaliadas if int(i[1:]) > 359]
    return Previsao(
        alvo=alvo,
        precisao=precisao,
        precisao_intervalo=precisao_intervalo,
        cobertura=cobertura,
        cobertura_intervalo=(percentil(coberturas, 0.025), percentil(coberturas, 0.975)),
        validacao=validacao,
        publicadas=sum(i in publicadas for i in avaliadas),
        avaliadas=len(avaliadas),
        cobertura_antigas=sum(i in publicadas for i in antigas) / max(len(antigas), 1),
        cobertura_novas=sum(i in publicadas for i in novas) / max(len(novas), 1),
    )


def texto_da_previsao(p: Previsao, tipo: str, modelo: str) -> str:
    v = p.validacao
    (pmin, pmax), (cmin, cmax) = p.precisao_intervalo, p.cobertura_intervalo
    return "\n".join(
        [
            f"precisao_prevista: {p.precisao:.2f}",
            f"precisao_intervalo: {pmin:.2f}-{pmax:.2f}",
            f"cobertura_prevista: {p.cobertura:.2f}",
            f"cobertura_intervalo: {min(cmin, p.cobertura):.2f}-{max(cmax, p.cobertura):.2f}",
            "",
            "Como chegamos nestes números",
            "",
            f"Sistema. Ranqueador '{tipo}' sobre embeddings '{modelo}' (locais, em cache), Temas "
            "enriquecidos, leis citadas, Origem e Questões vizinhas da Folha-verdade. Nenhum "
            "modelo de linguagem escolhe, vota ou valida o Tema.",
            "",
            f"Precisão. Validação cruzada estratificada (10 folds) nas 100 Questões da "
            f"Folha-verdade: cada uma foi pontuada por um Ranqueador que não a viu, e o kNN só "
            f"via as Questões de treino do fold. O limiar é o de maior cobertura em que a taxa "
            f"suavizada (Laplace) passa de {p.alvo:.2f} (ADR 0008): {v.acertos} certas de "
            f"{v.publicadas} publicadas fora do fold, ({v.acertos}+1)/({v.publicadas}+2) = "
            f"{p.precisao:.2f}. O intervalo une o de Wilson dessas publicadas ao bootstrap do "
            "procedimento (sorteia a Folha-verdade, escolhe o limiar e mede fora da reamostra).",
            "",
            f"Cobertura. Fração publicada nas {p.avaliadas} Questões fora da Folha-verdade: "
            f"{p.publicadas} de {p.avaliadas}. O intervalo vem dos limiares do bootstrap "
            "aplicados às pontuações dessas Questões.",
            "",
            "Por que pode errar. Os 100 rótulos são todos de Q0001 a Q0359, e 300 das "
            "avaliadas são novas. Nelas, a Origem aponta um Nó com bem menos frequência "
            f"(notebooks/01), e a cobertura muda: {p.cobertura_antigas:.2f} nas "
            f"antigas e {p.cobertura_novas:.2f} nas novas. A precisão nas novas pode ficar "
            "abaixo da medida na Folha-verdade, e o intervalo largo é a forma honesta de dizer "
            "isso com 100 rótulos.",
            "",
            "Coluna confianca do publicacao.csv. Em publicar e revisar, é a taxa de acerto "
            "suavizada da faixa de pontuação fora do fold (curva isotônica). Em fora, 0,50: a "
            "Folha-verdade não tem nenhuma Questão de disciplina militar para medir.",
            "",
        ]
    )
