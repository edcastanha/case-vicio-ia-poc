from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_folha_verdade, ler_questoes
from classificacao.v2.entrada import conhecimento as modulo

RAIZ = Path(__file__).parents[3]
ZIP = RAIZ / "anexos/v2/anexos-case-ia.zip"


def test_montador_sobre_os_artefatos_versionados_da_candidatos_validos(monkeypatch):
    monkeypatch.setattr(modulo, "DADOS", RAIZ / "dados/v2")
    conhecimento = modulo.carregar_conhecimento(ZIP, "bge-m3")
    questoes = ler_questoes(ZIP)[:3]
    sinais = modulo.montador(conhecimento)(questoes, ler_folha_verdade(ZIP))
    assert set(sinais) == {q.id for q in questoes}
    for candidatos in sinais.values():
        assert candidatos
        assert all(conhecimento.arvore.pode_receber_questao(c.no_id) for c in candidatos)
        assert all(-1.0 <= c.sinais.similaridade <= 1.0 for c in candidatos)
