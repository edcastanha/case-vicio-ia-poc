import json

from classificacao.adaptadores.arquivos import (
    CacheEmDisco,
    FilaDeFalhasEmArquivo,
    RegistroEmArquivo,
    gravar_propostas,
    ler_propostas,
)
from classificacao.aplicacao.classificar_questao import Classificacao, Proposta

CLASSIFICACAO = Classificacao(
    "Q0001",
    classificador=Proposta(10, 0.9, "júri", (100,), "classificador/v1@a"),
    verificador=Proposta(100, 0.8, "desaforamento", prompt="verificador/v1@b"),
    desempatador=None,
)


def test_cache_em_disco_sobrevive_a_uma_nova_instancia(tmp_path):
    CacheEmDisco(tmp_path).guardar("abc", {"no_id": 10})
    assert CacheEmDisco(tmp_path).obter("abc") == {"no_id": 10}
    assert CacheEmDisco(tmp_path).obter("outra") is None


def test_dlq_em_arquivo_acumula_uma_falha_por_linha(tmp_path):
    caminho = tmp_path / "falhas.jsonl"
    FilaDeFalhasEmArquivo(caminho).registrar("Q0001", "verificador", "fora do ar")
    FilaDeFalhasEmArquivo(caminho).registrar("Q0002", "lote", "bug")
    linhas = [json.loads(linha) for linha in caminho.read_text().splitlines()]
    assert [(f["questao_id"], f["papel"]) for f in linhas] == [
        ("Q0001", "verificador"),
        ("Q0002", "lote"),
    ]


def test_registro_em_arquivo_permite_retomar_e_devolve_as_classificacoes(tmp_path):
    caminho = tmp_path / "classificacoes.jsonl"
    RegistroEmArquivo(caminho).salvar(CLASSIFICACAO)
    retomado = RegistroEmArquivo(caminho)
    assert retomado.ja_classificada("Q0001")
    assert not retomado.ja_classificada("Q0002")
    assert retomado.todas() == [CLASSIFICACAO]


def test_registro_considera_feita_so_a_classificacao_completa(tmp_path):
    caminho = tmp_path / "classificacoes.jsonl"
    incompleta = Classificacao("Q0002", None, Proposta(10, 0.9, "v"), None)
    RegistroEmArquivo(caminho).salvar(incompleta)
    assert not RegistroEmArquivo(caminho).ja_classificada("Q0002")
    RegistroEmArquivo(caminho).salvar(CLASSIFICACAO)
    assert RegistroEmArquivo(caminho).ja_classificada("Q0001")


def test_linha_gravada_antes_do_versionamento_e_lida_sem_versao(tmp_path):
    caminho = tmp_path / "classificacoes.jsonl"
    legado = {"no_id": 10, "confianca": 0.9, "justificativa": "j", "extras": []}
    linha = {
        "questao_id": "Q0001",
        "classificador": legado,
        "verificador": legado,
        "desempatador": None,
    }
    caminho.write_text(json.dumps(linha) + "\n")
    [classificacao] = RegistroEmArquivo(caminho).todas()
    assert classificacao.classificador.prompt == ""


def test_propostas_gravadas_sao_lidas_de_volta(tmp_path):
    propostas = {
        "Q0002": Proposta(None, 0.6, "nenhum", prompt="rotulador/v1@c"),
        "Q0001": CLASSIFICACAO.classificador,
    }
    gravar_propostas(tmp_path / "rotulador.json", propostas)
    assert ler_propostas(tmp_path / "rotulador.json") == propostas
