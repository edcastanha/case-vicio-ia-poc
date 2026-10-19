import hashlib
from pathlib import Path

import pytest

from classificacao.adaptadores.prompts_em_arquivo import (
    PromptInexistente,
    carregar_prompt,
    carregar_prompts,
    ler_versoes_ativas,
)

PASTA = Path(__file__).parents[2] / "prompts"

# Uma versão publicada nunca muda: mudou o texto, é uma versão nova. Estes hashes são os textos
# que geraram a rodada completa das 359 Questões.
PUBLICADAS = {
    ("classificador", "v1"): "dce3cb015bed59a52c3e25b0afae8894c701101ffd3a99a94c9b2579dd3ada9b",
    ("verificador", "v1"): "7b8b74dbc3aca48b375ae7a186c432338f191ab2c5d3c60e3cf63013c99502b0",
    ("desempatador", "v1"): "c47bdf2def9bac9520725ab2c47fa2ee9e0941bd5c5520a5ae973c36cc9eec2a",
    ("rotulador", "v1"): "fc93cf7ae5296847a24bc8bf7e65054e1545aeaded49fa610ba490d5c7119b7f",
}


@pytest.mark.parametrize(("papel", "versao"), PUBLICADAS)
def test_versao_publicada_e_imutavel(papel, versao):
    texto = (PASTA / papel / f"{versao}.md").read_bytes()
    assert hashlib.sha256(texto).hexdigest() == PUBLICADAS[(papel, versao)]


def test_carrega_a_versao_ativa_de_cada_papel():
    prompts = carregar_prompts(PASTA, ler_versoes_ativas(PASTA))
    for papel in ("classificador", "verificador", "desempatador"):
        prompt = getattr(prompts, papel)
        assert (prompt.papel, prompt.versao) == (papel, "v1")
        assert prompt.texto == (PASTA / papel / "v1.md").read_text()


def test_versao_ativa_pode_ser_trocada_por_papel(tmp_path):
    for papel in ("classificador", "verificador", "desempatador"):
        (tmp_path / papel).mkdir()
        (tmp_path / papel / "v1.md").write_text(f"{papel} v1\n")
    (tmp_path / "classificador" / "v2.md").write_text("classificador v2\n")
    versoes = {"classificador": "v2", "verificador": "v1", "desempatador": "v1"}
    prompts = carregar_prompts(tmp_path, versoes)
    assert prompts.classificador.texto == "classificador v2\n"
    assert prompts.verificador.texto == "verificador v1\n"


def test_versao_que_nao_existe_falha_com_o_caminho(tmp_path):
    with pytest.raises(PromptInexistente, match="classificador/v9.md"):
        carregar_prompts(
            tmp_path, {"classificador": "v9", "verificador": "v1", "desempatador": "v1"}
        )


def test_versoes_ativas_exigem_os_tres_papeis(tmp_path):
    (tmp_path / "versoes.toml").write_text('classificador = "v1"\n')
    with pytest.raises(PromptInexistente, match="verificador"):
        ler_versoes_ativas(tmp_path)


def test_rotulador_tem_versao_ativa_propria_fora_dos_papeis_do_pipeline():
    versao = ler_versoes_ativas(PASTA)["rotulador"]
    prompt = carregar_prompt(PASTA, "rotulador", versao)
    assert prompt.rotulo.startswith("rotulador/v1@")
