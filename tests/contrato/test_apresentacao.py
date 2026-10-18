"""O deck do site (docs/apresentacao/) não pode divergir dos dados nem de si mesmo."""

import csv
import json
import re
from collections import Counter
from pathlib import Path

import pytest

from classificacao.adaptadores.anexos import ler_arvore
from classificacao.adaptadores.arquivos import RegistroEmArquivo
from classificacao.adaptadores.rotulagem import ler_rotulos
from classificacao.aplicacao.calibrar_com_rotulos import rotulos_de_calibracao
from classificacao.aplicacao.classificar_questao import situacao
from classificacao.aplicacao.gerar_entrega import Sinais

RAIZ = Path(__file__).parents[2]
DECK = RAIZ / "docs/apresentacao"
COMPOSICAO = (DECK / "composition/index.html").read_text()
WRAPPER = (DECK / "index.html").read_text()


def _ilha(html: str) -> dict:
    bloco = re.search(
        r'<script type="application/hyperframes-slideshow\+json">(.*?)</script>', html, re.S
    )
    return json.loads(bloco.group(1))


def _bloco_json(id: str) -> dict:
    bloco = re.search(
        rf'<script type="application/json" id="{id}">(.*?)</script>', COMPOSICAO, re.S
    )
    return json.loads(bloco.group(1))


def _dados_do_deck() -> dict:
    return _bloco_json("dados-da-entrega")


def test_wrapper_tem_copia_identica_do_island_da_composicao():
    # O <hyperframes-slideshow> lê o island do próprio wrapper, não da composição.
    assert _ilha(WRAPPER) == _ilha(COMPOSICAO)


def test_cada_slide_do_island_aponta_para_uma_cena_e_as_cenas_sao_avisadas_ao_slideshow():
    cenas = {
        id: (int(inicio), int(duracao))
        for id, inicio, duracao in re.findall(
            r'data-composition-id="(\w+)"\s+data-start="(\d+)"\s+data-duration="(\d+)"', COMPOSICAO
        )
    }
    cenas.pop("root")
    ilha = _ilha(COMPOSICAO)
    usadas = [s["sceneId"] for s in ilha["slides"]]
    usadas += [s["sceneId"] for seq in ilha["slideSequences"] for s in seq["slides"]]
    assert sorted(usadas) == sorted(cenas)
    avisadas = re.findall(r'\{ id: "(\w+)", start: (\d+), duration: (\d+) \}', COMPOSICAO)
    assert {id: (int(i), int(d)) for id, i, d in avisadas} == cenas


def test_tempos_das_etapas_no_script_sao_os_do_island():
    do_island = sorted(t for s in _ilha(COMPOSICAO)["slides"] for t in s.get("fragments", []))
    do_script = sorted(float(t) for t in re.findall(r"\{ time: ([\d.]+), ids:", COMPOSICAO))
    assert do_script == do_island


@pytest.fixture(scope="module")
def medido() -> dict:
    """Os mesmos números, recalculados dos arquivos da entrega."""
    arvore = ler_arvore(RAIZ / "anexos-case-ia.zip")
    classificacoes = {
        c.questao_id: c
        for c in RegistroEmArquivo(RAIZ / "dados/rodada/classificacoes.jsonl").todas()
    }
    situacoes = Counter(situacao(c, arvore) for c in classificacoes.values())
    with (RAIZ / "publicacao.csv").open(newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    decisoes = Counter(linha["decisao"] for linha in linhas)
    motivos = Counter(linha["motivo"] for linha in linhas)
    previsao = dict(
        linha.split(": ") for linha in (RAIZ / "previsao.txt").read_text().splitlines()[:4]
    )
    minimo, maximo = (float(v) for v in previsao["precisao_intervalo"].split("-"))
    rotulos = ler_rotulos(RAIZ / "dados/rotulagem.csv", arvore)
    brutos = json.loads((RAIZ / "dados/rodada/sinais.json").read_text())
    sinais = {id: Sinais(**valores) for id, valores in brutos.items()}
    desacordos = [id for id in rotulos if situacao(classificacoes[id], arvore) == "desacordo"]
    juiz_no_ramo = sum(
        classificacoes[id].juiz is not None
        and classificacoes[id].juiz.no_id is not None
        and arvore.mesmo_ramo(classificacoes[id].juiz.no_id, rotulos[id])
        for id in desacordos
    )
    return {
        "total": len(linhas),
        "publicar": decisoes["publicar"],
        "revisar": decisoes["revisar"],
        "fora": decisoes["fora"],
        "concordancia": situacoes["mesmo no"] + situacoes["mesmo ramo"],
        "desacordo": situacoes["desacordo"],
        "tema_duplicado": motivos["tema duplicado na árvore"],
        "duvida": motivos["um dos modelos declarou dúvida"],
        "precisao": float(previsao["precisao_prevista"]),
        "precisao_min": minimo,
        "precisao_max": maximo,
        "cobertura": float(previsao["cobertura_prevista"]),
        "calibracao": len(rotulos_de_calibracao(classificacoes, rotulos, arvore, sinais)),
        "desacordos_na_amostra": len(desacordos),
        "juiz_no_ramo": juiz_no_ramo,
    }


def test_numeros_do_deck_sao_os_da_entrega(medido):
    assert _dados_do_deck() == medido


def test_projecao_de_producao_sai_das_premissas_do_adr_0007_e_dos_numeros_da_entrega():
    p, entrega = _bloco_json("projecao-de-producao"), _dados_do_deck()
    deepseek = p["custo_deepseek"] / p["requisicoes_deepseek"]  # painel da DeepSeek, README
    classificador = p["custo_piloto_classificador"] / p["questoes_do_piloto"]  # claude -p
    fator = p["fator_dos_candidatos"]
    assert p["desacordo"] == round((entrega["desacordo"] + entrega["fora"]) / entrega["total"], 2)
    assert p["fila_por_semana"] == round(entrega["revisar"] / entrega["total"] * 50_000, -3)
    hoje = classificador + p["custo_deepseek"] / entrega["total"]
    fase1 = (classificador + deepseek) / fator + entrega["desacordo"] / entrega[
        "total"
    ] * deepseek / fator
    fase2 = (
        p["embeddings_por_questao"]
        + deepseek / fator
        + p["desacordo"] * (classificador + deepseek) / fator
    )
    for chave, valor in {"hoje": hoje, "fase1": fase1, "fase2": fase2}.items():
        assert p[chave] == pytest.approx(valor, rel=0.03), chave
        assert p[f"{chave}_semana"] == pytest.approx(valor * p["questoes_por_semana"], rel=0.02), (
            chave
        )
