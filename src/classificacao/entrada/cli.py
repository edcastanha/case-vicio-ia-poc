import argparse
import csv
import random
from pathlib import Path

from classificacao.adaptadores.anexos import ler_arvore, ler_questoes
from classificacao.adaptadores.arquivos import (
    CacheEmDisco,
    FilaDeFalhasEmArquivo,
    RegistroEmArquivo,
)
from classificacao.aplicacao.processar_lote import processar_lote
from classificacao.dominio.arvore import Arvore
from classificacao.entrada.configuracao import carregar_env, criar_papeis

ZIP_PADRAO = Path("anexos-case-ia.zip")


def main() -> None:
    parser = argparse.ArgumentParser(prog="classificacao")
    comandos = parser.add_subparsers(dest="comando", required=True)
    piloto = comandos.add_parser("piloto", help="classifica uma amostra sorteada de questões")
    piloto.add_argument("--n", type=int, default=30)
    piloto.add_argument("--semente", type=int, default=42)
    piloto.add_argument("--paralelismo", type=int, default=2)
    piloto.add_argument("--saida", type=Path, default=Path("dados/piloto"))
    piloto.add_argument("--zip", type=Path, default=ZIP_PADRAO)
    argumentos = parser.parse_args()

    carregar_env()
    if argumentos.comando == "piloto":
        rodar_piloto(argumentos)


def rodar_piloto(argumentos: argparse.Namespace) -> None:
    arvore = ler_arvore(argumentos.zip)
    todas = ler_questoes(argumentos.zip)
    amostra = sorted(
        random.Random(argumentos.semente).sample(todas, argumentos.n), key=lambda q: q.id
    )
    papeis = criar_papeis()
    saida: Path = argumentos.saida
    registro = RegistroEmArquivo(saida / "classificacoes.jsonl")
    processar_lote(
        amostra,
        arvore,
        papeis,
        registro=registro,
        fila_de_falhas=FilaDeFalhasEmArquivo(saida / "falhas.jsonl"),
        cache=CacheEmDisco(Path("dados/cache")),
        paralelismo=argumentos.paralelismo,
    )
    escrever_resumo(registro, arvore, saida / "resumo.csv")
    custo = sum(getattr(m, "custo_usd", 0.0) for m in vars(papeis).values())
    classificadas = len(registro.todas())
    print(f"{classificadas}/{len(amostra)} classificadas; custo desta execução US$ {custo:.2f}")
    print(f"resumo: {saida / 'resumo.csv'}")


def escrever_resumo(registro: RegistroEmArquivo, arvore: Arvore, caminho: Path) -> None:
    def caminho_do(no_id: int | None) -> str:
        if no_id is None:
            return "(nenhum nó serve)"
        no = arvore.no(no_id)
        return no.caminho if no else f"(id inexistente {no_id})"

    with caminho.open("w", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            ["id", "situacao", "papel", "no_id", "caminho", "confianca", "justificativa"]
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
