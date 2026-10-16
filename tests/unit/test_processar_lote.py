from classificacao.aplicacao.classificar_questao import Papeis
from classificacao.aplicacao.processar_lote import processar_lote
from classificacao.dominio.questao import Questao
from tests.unit.fakes import (
    CacheEmMemoria,
    FilaDeFalhasEmMemoria,
    ModeloFake,
    RegistroEmMemoria,
    sempre,
)
from tests.unit.test_classificar_questao import ARVORE


def questao(id: str) -> Questao:
    return Questao(id, f"enunciado {id}", "comando", {"A": "a"}, "Processo Penal", "Júri")


def processar(questoes, registro, papeis=None, fila=None):
    papeis = papeis or Papeis(
        ModeloFake("c", sempre(10)), ModeloFake("v", sempre(10)), ModeloFake("j", sempre(10))
    )
    return processar_lote(
        questoes,
        ARVORE,
        papeis,
        registro=registro,
        fila_de_falhas=fila or FilaDeFalhasEmMemoria(),
        cache=CacheEmMemoria(),
        esperar=lambda tentativa: None,
    )


def test_todas_as_questoes_do_lote_terminam_registradas():
    registro = RegistroEmMemoria()
    processar([questao("Q0001"), questao("Q0002"), questao("Q0003")], registro)
    assert set(registro.classificacoes) == {"Q0001", "Q0002", "Q0003"}


def test_questao_ja_classificada_nao_e_processada_de_novo():
    registro = RegistroEmMemoria()
    processar([questao("Q0001")], registro)
    classificador = ModeloFake("c", sempre(10))
    papeis = Papeis(classificador, ModeloFake("v", sempre(10)), ModeloFake("j", sempre(10)))
    processar([questao("Q0001"), questao("Q0002")], registro, papeis=papeis)
    assert len(classificador.chamadas) == 1
    assert set(registro.classificacoes) == {"Q0001", "Q0002"}


def test_erro_inesperado_numa_questao_nao_derruba_o_lote():
    def explode_na_q0002(sistema: str, usuario: str) -> dict:
        if "Q0002" in usuario:
            raise RuntimeError("bug no adaptador")
        return sempre(10)(sistema, usuario)

    registro = RegistroEmMemoria()
    fila = FilaDeFalhasEmMemoria()
    papeis = Papeis(
        ModeloFake("c", explode_na_q0002), ModeloFake("v", sempre(10)), ModeloFake("j", sempre(10))
    )
    processar([questao("Q0001"), questao("Q0002"), questao("Q0003")], registro, papeis, fila)
    assert set(registro.classificacoes) == {"Q0001", "Q0003"}
    assert [(q, papel) for q, papel, _ in fila.falhas] == [("Q0002", "lote")]


def test_com_paralelismo_todas_as_questoes_terminam_registradas():
    registro = RegistroEmMemoria()
    questoes = [questao(f"Q{i:04d}") for i in range(1, 21)]
    processar_lote(
        questoes,
        ARVORE,
        Papeis(
            ModeloFake("c", sempre(10)), ModeloFake("v", sempre(11)), ModeloFake("j", sempre(10))
        ),
        registro=registro,
        fila_de_falhas=FilaDeFalhasEmMemoria(),
        cache=CacheEmMemoria(),
        esperar=lambda tentativa: None,
        paralelismo=2,
    )
    assert set(registro.classificacoes) == {q.id for q in questoes}
