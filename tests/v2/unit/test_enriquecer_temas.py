from classificacao.nucleo.dominio.arvore import Arvore, No
from classificacao.v2.aplicacao.enriquecer_temas import enriquecer_temas, lotes_por_tema
from classificacao.v2.aplicacao.portas import FalhaDoModelo

ARVORE = Arvore(
    [
        No(1, None, 0, "Penal"),
        No(10, 1, 1, "Penal > Teoria da Pena"),
        No(100, 10, 2, "Penal > Teoria da Pena > Pena de Multa"),
        No(11, 1, 1, "Penal > Prescrição"),
        No(12, 1, 1, "Penal > Inativo", ativo=False),
    ]
)


def item(no_id):
    return {"id": no_id, "descricao": f"d{no_id}", "nao_entra": "", "termos": ["T"], "leis": []}


class ModeloQueDescreve:
    identificador = "fake"

    def __init__(self, falhas=0):
        self.pedidos, self.falhas = [], falhas

    def responder(self, sistema, usuario, schema):
        self.pedidos.append(usuario)
        if self.falhas:
            self.falhas -= 1
            raise FalhaDoModelo("fora do ar")
        ids = [
            int(linha[1 : linha.index("]")])
            for linha in usuario.split("## Nós a descrever\n")[1].splitlines()
        ]
        return {"nos": [item(i) for i in ids]}


def test_lotes_seguem_o_caminho_e_deixam_de_fora_disciplina_e_inativo():
    assert [[no.id for no in lote] for lote in lotes_por_tema(ARVORE, 2)] == [[11, 10], [100]]


def test_descreve_so_o_que_falta_e_o_modelo_ve_a_arvore_mas_nenhuma_questao():
    guardados, modelo = [], ModeloQueDescreve()
    falhas = enriquecer_temas(
        ARVORE, modelo, "sistema", "enriquecedor/v1@x", [11], guardados.extend
    )
    assert falhas == []
    assert [(t.no_id, t.termos, t.prompt) for t in guardados] == [
        (10, ("t",), "enriquecedor/v1@x"),
        (100, ("t",), "enriquecedor/v1@x"),
    ]
    assert "## Árvore\n[11] Penal > Prescrição" in modelo.pedidos[0]
    assert "[11]" not in modelo.pedidos[0].split("## Nós a descrever")[1]


def test_tenta_de_novo_e_devolve_os_ids_do_lote_que_falhou_sempre():
    guardados = []
    assert (
        enriquecer_temas(ARVORE, ModeloQueDescreve(falhas=1), "s", "r", [], guardados.extend) == []
    )
    assert enriquecer_temas(ARVORE, ModeloQueDescreve(falhas=9), "s", "r", [], [].append) == [
        11,
        10,
        100,
    ]
