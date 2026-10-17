import argparse
import csv
import json
import random
from pathlib import Path

from classificacao.adaptadores.anexos import ler_arvore, ler_questoes
from classificacao.adaptadores.arquivos import (
    CacheEmDisco,
    FilaDeFalhasEmArquivo,
    RegistroEmArquivo,
)
from classificacao.adaptadores.rotulagem import escrever_planilha, ler_rotulos
from classificacao.aplicacao.amostra_cega import gerar_amostra_cega
from classificacao.aplicacao.calcular_sinais import calcular_sinais
from classificacao.aplicacao.calibrar_com_rotulos import rotulos_de_calibracao
from classificacao.aplicacao.gerar_entrega import Sinais, gerar_entrega
from classificacao.aplicacao.processar_lote import processar_lote
from classificacao.aplicacao.prompts import VersoesDePromptMisturadas, exigir_versao_unica
from classificacao.dominio.arvore import Arvore
from classificacao.dominio.calibracao import ajustar_curva, calibrar, estimar_precisao
from classificacao.dominio.questao import Questao
from classificacao.entrada.configuracao import (
    carregar_env,
    criar_embeddings,
    criar_papeis,
    criar_prompts,
)

ZIP_PADRAO = Path("anexos-case-ia.zip")
RODADA = Path("dados/rodada")
ALVO_DE_PRECISAO = 0.97  # ADR 0002: margem sobre a Régua de 95%


def main() -> None:
    parser = argparse.ArgumentParser(prog="classificacao")
    parser.add_argument("--zip", type=Path, default=ZIP_PADRAO)
    comandos = parser.add_subparsers(dest="comando", required=True)

    piloto = comandos.add_parser("piloto", help="classifica uma amostra sorteada de questões")
    piloto.add_argument("--n", type=int, default=30)
    piloto.add_argument("--semente", type=int, default=42)
    piloto.add_argument("--paralelismo", type=int, default=2)
    piloto.add_argument("--saida", type=Path, default=Path("dados/piloto"))

    rodada = comandos.add_parser("rodada", help="classifica as 359 questões (retomável)")
    rodada.add_argument("--paralelismo", type=int, default=2)

    comandos.add_parser("sinais", help="calcula similaridade e reserva pelos embeddings")

    amostra = comandos.add_parser("amostra", help="gera a planilha cega de rotulagem")
    amostra.add_argument("--n", type=int, default=50)
    amostra.add_argument("--semente", type=int, default=7)
    amostra.add_argument("--saida", type=Path, default=Path("dados/rotulagem.csv"))

    entrega = comandos.add_parser("entrega", help="calibra nos rótulos e gera a entrega")
    entrega.add_argument("--rotulos", type=Path, default=Path("dados/rotulagem.csv"))
    entrega.add_argument("--repeticoes", type=int, default=1000)

    argumentos = parser.parse_args()
    carregar_env()
    {
        "piloto": rodar_piloto,
        "rodada": rodar_rodada,
        "sinais": rodar_sinais,
        "amostra": rodar_amostra,
        "entrega": rodar_entrega,
    }[argumentos.comando](argumentos)


def rodar_piloto(argumentos: argparse.Namespace) -> None:
    todas = ler_questoes(argumentos.zip)
    amostra = sorted(
        random.Random(argumentos.semente).sample(todas, argumentos.n), key=lambda q: q.id
    )
    _classificar(amostra, argumentos.zip, argumentos.saida, argumentos.paralelismo)


def rodar_rodada(argumentos: argparse.Namespace) -> None:
    _classificar(ler_questoes(argumentos.zip), argumentos.zip, RODADA, argumentos.paralelismo)


def _classificar(questoes: list[Questao], zip_anexos: Path, saida: Path, paralelismo: int) -> None:
    arvore = ler_arvore(zip_anexos)
    papeis = criar_papeis()
    prompts = criar_prompts()
    print("prompts: " + ", ".join(p.rotulo for p in vars(prompts).values()))
    registro = RegistroEmArquivo(saida / "classificacoes.jsonl")
    processar_lote(
        questoes,
        arvore,
        papeis,
        prompts,
        registro=registro,
        fila_de_falhas=FilaDeFalhasEmArquivo(saida / "falhas.jsonl"),
        cache=CacheEmDisco(Path("dados/cache")),
        paralelismo=paralelismo,
    )
    escrever_resumo(registro, arvore, saida / "resumo.csv")
    custo = sum(getattr(m, "custo_usd", 0.0) for m in vars(papeis).values())
    for papel, modelo in vars(papeis).items():
        if hasattr(modelo, "tokens"):
            print(f"tokens {papel} ({modelo.identificador}): {modelo.tokens}")
    classificadas = len(registro.todas())
    print(f"{classificadas}/{len(questoes)} classificadas; custo desta execução US$ {custo:.2f}")
    print(f"resumo: {saida / 'resumo.csv'}")


def rodar_sinais(argumentos: argparse.Namespace) -> None:
    arvore = ler_arvore(argumentos.zip)
    classificacoes = {
        c.questao_id: c for c in RegistroEmArquivo(RODADA / "classificacoes.jsonl").todas()
    }
    sinais = calcular_sinais(
        ler_questoes(argumentos.zip), arvore, classificacoes, criar_embeddings()
    )
    caminho = RODADA / "sinais.json"
    caminho.write_text(
        json.dumps({id: vars(s) for id, s in sinais.items()}, ensure_ascii=False, indent=1)
    )
    print(f"sinais de {len(sinais)} questões: {caminho}")


def rodar_amostra(argumentos: argparse.Namespace) -> None:
    arvore = ler_arvore(argumentos.zip)
    questoes = {q.id: q for q in ler_questoes(argumentos.zip)}
    classificacoes = RegistroEmArquivo(RODADA / "classificacoes.jsonl").todas()
    itens = gerar_amostra_cega(
        classificacoes, questoes, arvore, n=argumentos.n, semente=argumentos.semente
    )
    escrever_planilha(itens, arvore, argumentos.saida)
    print(f"{len(itens)} questões para rotular: {argumentos.saida}")


def rodar_entrega(argumentos: argparse.Namespace) -> None:
    arvore = ler_arvore(argumentos.zip)
    ids = [q.id for q in ler_questoes(argumentos.zip)]
    classificacoes = {
        c.questao_id: c for c in RegistroEmArquivo(RODADA / "classificacoes.jsonl").todas()
    }
    try:
        versoes = exigir_versao_unica(classificacoes.values())
    except VersoesDePromptMisturadas as erro:
        raise SystemExit(
            f"rodada inconsistente, refaça com uma versão por prompt: {erro}"
        ) from erro
    print("prompts da rodada: " + ", ".join(versoes))
    sinais = _ler_sinais(RODADA / "sinais.json")
    rotulos = ler_rotulos(argumentos.rotulos, arvore)
    pares = rotulos_de_calibracao(classificacoes, rotulos, arvore, sinais)
    calibracao = calibrar(pares, alvo=ALVO_DE_PRECISAO)
    estimativa = estimar_precisao(
        pares, alvo=ALVO_DE_PRECISAO, repeticoes=argumentos.repeticoes, semente=1
    )
    if estimativa is None:
        raise SystemExit("nenhuma reamostragem publicou nada: rótulos insuficientes ou ruins")
    entrega = gerar_entrega(
        ids,
        classificacoes,
        arvore,
        sinais,
        limiar_de_pontuacao=calibracao.limiar,
        curva=ajustar_curva(pares, faixas=5),
        estimativa=estimativa,
    )
    with Path("publicacao.csv").open("w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(entrega.linhas[0]))
        escritor.writeheader()
        escritor.writerows(entrega.linhas)
    Path("previsao.txt").write_text(entrega.previsao)
    print(
        f"{len(rotulos)} rótulos, {len(pares)} na calibração; limiar {calibracao.limiar}; "
        f"precisão na amostra {calibracao.precisao_prevista:.3f}, "
        f"bootstrap {estimativa.precisao:.3f}"
    )
    print(entrega.previsao)


def _ler_sinais(caminho: Path) -> dict[str, Sinais]:
    if not caminho.exists():
        print(f"aviso: {caminho} não existe; seguindo sem similaridade nem reserva")
        return {}
    return {id: Sinais(**valores) for id, valores in json.loads(caminho.read_text()).items()}


def escrever_resumo(registro: RegistroEmArquivo, arvore: Arvore, caminho: Path) -> None:
    def caminho_do(no_id: int | None) -> str:
        if no_id is None:
            return "(nenhum nó serve)"
        no = arvore.no(no_id)
        return no.caminho if no else f"(id inexistente {no_id})"

    with caminho.open("w", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            ["id", "situacao", "papel", "no_id", "caminho", "confianca", "justificativa", "prompt"]
        )
        for c in sorted(registro.todas(), key=lambda c: c.questao_id):
            situacao = _situacao(c, arvore)
            for papel in ("classificador", "verificador", "juiz"):
                proposta = getattr(c, papel)
                if proposta is not None:
                    escritor.writerow(
                        [
                            c.questao_id,
                            situacao,
                            papel,
                            proposta.no_id,
                            caminho_do(proposta.no_id),
                            proposta.confianca,
                            proposta.justificativa,
                            proposta.prompt,
                        ]
                    )


def _situacao(c, arvore: Arvore) -> str:
    if c.classificador is None or c.verificador is None:
        return "falha"
    a, b = c.classificador.no_id, c.verificador.no_id
    if a is None and b is None:
        return "fora"
    if a == b and arvore.pode_receber_questao(a):
        return "mesmo no"
    if arvore.no_de_consenso(a, b) is not None:
        return "mesmo ramo"
    return "desacordo"


if __name__ == "__main__":
    main()
