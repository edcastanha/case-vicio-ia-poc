import re
from pathlib import Path

from classificacao.nucleo.adaptadores.anexos import ler_arvore
from classificacao.v2.adaptadores import cache_de_embeddings
from classificacao.v2.adaptadores.cache_de_embeddings import sha256_dos_textos
from classificacao.v2.dominio.temas import texto_do_tema
from classificacao.v2.entrada import conhecimento as modulo

RAIZ = Path(__file__).parents[3]
ARVORE = ler_arvore(RAIZ / "anexos/v2/anexos-case-ia.zip")
DISCIPLINAS = ("Penal", "Processo Penal", "Direito Penal - Legislação Especial", "Criminologia")


def test_todo_caminho_citado_nos_temas_revisados_existe_na_arvore(monkeypatch):
    monkeypatch.setattr(modulo, "DADOS", RAIZ / "dados/v2")
    caminhos = sorted((no.caminho for no in ARVORE.nos_que_podem_receber_questao()), key=len)
    inicio = re.compile(rf"(?:{'|'.join(DISCIPLINAS)}) > ")
    for no_id, tema in modulo.temas_revisados().items():
        for texto in (tema.descricao, tema.nao_entra):
            fim_da_ultima = 0
            for citacao in inicio.finditer(texto):
                if citacao.start() < fim_da_ultima:
                    continue  # "Penal > " dentro de "Processo Penal > Ação Penal > ..."
                resto = texto[citacao.start() :]
                maior = max((c for c in caminhos if resto.startswith(c)), key=len, default="")
                # o caminho citado é um Nó da Árvore e não continua com mais um nível inventado
                assert maior and not resto[len(maior) :].startswith(" > "), (no_id, resto[:90])
                fim_da_ultima = citacao.start() + len(maior)


def test_os_vetores_dos_nos_foram_gerados_dos_temas_ja_corrigidos(monkeypatch):
    monkeypatch.setattr(modulo, "DADOS", RAIZ / "dados/v2")
    temas = modulo.temas_revisados()
    nos = sorted(ARVORE.nos_que_podem_receber_questao(), key=lambda no: no.id)
    textos = [texto_do_tema(no, temas[no.id]) for no in nos]
    for modelo in ("bge-m3", "e5-base"):
        _, _, manifesto = cache_de_embeddings.ler(RAIZ / "dados/v2/embeddings" / modelo, "nos")
        assert manifesto["textos_sha256"] == sha256_dos_textos(textos), modelo
