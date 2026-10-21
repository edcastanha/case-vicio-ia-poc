import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore, ler_questoes
from classificacao.v2.adaptadores import cache_de_embeddings
from classificacao.v2.adaptadores.cache_de_embeddings import sha256_dos_textos
from classificacao.v2.adaptadores.dicionarios import ler_temas_enriquecidos
from classificacao.v2.aplicacao.enriquecer_temas import (
    enriquecer_temas,
    para_json,
    rotulo_do_prompt,
)
from classificacao.v2.dominio.temas import texto_do_tema
from classificacao.v2.dominio.textos import texto_da_questao

ZIP_PADRAO = Path("anexos/v2/anexos-case-ia.zip")
DADOS = Path("dados/v2")
PROMPTS = Path("prompts/v2")
TEMAS_ENRIQUECIDOS = DADOS / "temas_enriquecidos.jsonl"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="classificacao v2")
    parser.add_argument("--zip", type=Path, default=ZIP_PADRAO)
    comandos = parser.add_subparsers(dest="comando", required=True)
    enriquecer = comandos.add_parser(
        "enriquecer",
        help="descreve os Nós com um modelo de linguagem (antes da decisão; retomável)",
    )
    enriquecer.add_argument("--modelo", default="sonnet")
    enriquecer.add_argument("--versao", default="v1")
    enriquecer.add_argument("--lote", type=int, default=20)
    embeddings = comandos.add_parser(
        "embeddings", help="gera o cache de vetores com um modelo local (antes da decisão)"
    )
    embeddings.add_argument("--modelo", choices=["bge-m3", "e5-base"], default="bge-m3")
    embeddings.add_argument("--parte", choices=["questoes", "nos", "tudo"], default="tudo")
    comparar = comandos.add_parser(
        "comparar", help="compara Ranqueadores e embeddings por validação cruzada (sem modelo)"
    )
    comparar.add_argument("--modelos", nargs="+", default=["bge-m3", "e5-base"])
    comparar.add_argument("--tipos", nargs="+", default=["similaridade", "knn", "logistica", "mlp"])
    entrega = comandos.add_parser(
        "entrega", help="gera publicacao.csv e previsao.txt só com artefatos versionados"
    )
    entrega.add_argument("--saida", type=Path, default=Path("."))
    entrega.add_argument("--repeticoes", type=int, default=1000)
    argumentos = parser.parse_args(argv)
    {
        "entrega": rodar_entrega,
        "enriquecer": rodar_enriquecimento,
        "embeddings": rodar_embeddings,
        "comparar": rodar_comparacao,
    }[argumentos.comando](argumentos)


def rodar_enriquecimento(argumentos: argparse.Namespace) -> None:
    from classificacao.v2.adaptadores.claude_code import ModeloClaudeCode

    texto = (PROMPTS / "enriquecedor" / f"{argumentos.versao}.md").read_text()
    rotulo = rotulo_do_prompt(texto, argumentos.versao)
    feitos = ler_temas_enriquecidos(TEMAS_ENRIQUECIDOS)
    if any(tema.prompt != rotulo for tema in feitos.values()):
        raise SystemExit(f"{TEMAS_ENRIQUECIDOS} tem outra versão do prompt; apague para refazer")
    TEMAS_ENRIQUECIDOS.parent.mkdir(parents=True, exist_ok=True)

    def guardar(temas):
        # fsync por lote: se a máquina cair no meio, o arquivo não fica com uma linha pela metade.
        with TEMAS_ENRIQUECIDOS.open("a") as arquivo:
            arquivo.writelines(para_json(tema) + "\n" for tema in temas)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        print(f"+{len(temas)} Nós ({rotulo})", flush=True)

    falhas = enriquecer_temas(
        ler_arvore(argumentos.zip),
        ModeloClaudeCode(argumentos.modelo),
        texto,
        rotulo,
        feitos,
        guardar,
        tamanho_do_lote=argumentos.lote,
    )
    total = len(ler_temas_enriquecidos(TEMAS_ENRIQUECIDOS))
    print(f"{total} Nós descritos em {TEMAS_ENRIQUECIDOS}; falharam: {falhas or 'nenhum'}")


def rodar_embeddings(argumentos: argparse.Namespace) -> None:
    from classificacao.v2.adaptadores import embeddings_locais

    modelo = embeddings_locais.MODELOS[argumentos.modelo]
    pasta = DADOS / "embeddings" / modelo.nome
    base = {
        "modelo": modelo.repositorio,
        "revisao": embeddings_locais.revisao(modelo),
        "tamanho_maximo": modelo.tamanho_maximo,
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    if argumentos.parte in ("questoes", "tudo"):
        questoes = ler_questoes(argumentos.zip)
        textos = [texto_da_questao(q) for q in questoes]
        vetores = embeddings_locais.vetorizar(modelo, textos, modelo.prefixo_da_questao)
        manifesto = base | {"textos_sha256": sha256_dos_textos(textos), "zip": str(argumentos.zip)}
        cache_de_embeddings.gravar(pasta, "questoes", [q.id for q in questoes], vetores, manifesto)
        print(f"{len(questoes)} Questões → {pasta}/questoes.npy")
    if argumentos.parte in ("nos", "tudo"):
        arvore = ler_arvore(argumentos.zip)
        temas = ler_temas_enriquecidos(TEMAS_ENRIQUECIDOS)
        nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.id)
        faltando = [no.id for no in nos if no.id not in temas]
        if faltando:
            raise SystemExit(f"{len(faltando)} Nós sem tema enriquecido; rode `enriquecer` antes")
        textos = [texto_do_tema(no, temas[no.id]) for no in nos]
        vetores = embeddings_locais.vetorizar(modelo, textos, modelo.prefixo_do_tema)
        prompts = sorted({tema.prompt for tema in temas.values()})
        manifesto = base | {"textos_sha256": sha256_dos_textos(textos), "enriquecimento": prompts}
        cache_de_embeddings.gravar(pasta, "nos", [no.id for no in nos], vetores, manifesto)
        print(f"{len(nos)} Nós → {pasta}/nos.npy")


ALVO = 0.97  # ADR 0008: taxa suavizada com margem sobre a Régua de 95%


def rodar_comparacao(argumentos: argparse.Namespace) -> None:
    import json
    from functools import partial

    from classificacao.nucleo.adaptadores.anexos import ler_folha_verdade
    from classificacao.v2.aplicacao.montar_sinais import montar_sinais
    from classificacao.v2.aplicacao.validacao_cruzada import validar
    from classificacao.v2.entrada.conhecimento import carregar_conhecimento

    questoes = {q.id: q for q in ler_questoes(argumentos.zip)}
    folha = ler_folha_verdade(argumentos.zip)
    linhas = []
    for modelo in argumentos.modelos:
        conhecimento = carregar_conhecimento(argumentos.zip, modelo)
        montar = partial(montar_sinais, conhecimento=conhecimento)
        for tipo in argumentos.tipos:
            r = validar(tipo, conhecimento.arvore, questoes, folha, montar, ALVO)
            linha = {
                "embeddings": modelo,
                "ranqueador": tipo,
                "acerto_do_top1": sum(p.acertou for p in r.previsoes) / len(r.previsoes),
                "limiar": r.limiar,
                "publicadas": r.publicadas,
                "acertos": r.acertos,
                "cobertura": r.cobertura,
                "precisao_suavizada": r.precisao_suavizada,
            }
            linhas.append(linha)
            print(json.dumps(linha, ensure_ascii=False), flush=True)
    (DADOS / "comparacao.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1) + "\n")


def rodar_entrega(argumentos: argparse.Namespace) -> None:
    from classificacao.v2.entrada import entrega

    entrega.rodar(argumentos.zip, argumentos.saida, argumentos.repeticoes)
