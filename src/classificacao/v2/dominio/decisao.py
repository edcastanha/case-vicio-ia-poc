"""A decisão da v2: só o Ranqueador e as regras abaixo, sem nenhum modelo de linguagem."""

from collections.abc import Sequence
from dataclasses import dataclass

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.decisao import Decisao, Resultado
from classificacao.v2.dominio.leis import normalizar


@dataclass(frozen=True)
class Pontuado:
    no_id: int
    pontuacao: float
    voto_das_vizinhas: float


def decidir(
    arvore: Arvore, escolhido: Pontuado, limiar: float | None, disciplina_origem: str
) -> Resultado:
    # A árvore não tem Direito Penal Militar; as demais disciplinas de origem erradas
    # não bastam para Fora (Q0016 vem como Constitucional e é sobre prisão).
    if "militar" in normalizar(disciplina_origem):
        motivo = f"disciplina de origem fora da árvore ({disciplina_origem})"
        return Resultado(Decisao.FORA, None, motivo)
    if arvore.em_tema_duplicado(escolhido.no_id) and escolhido.voto_das_vizinhas == 0:
        motivo = "tema duplicado sem exemplo da equipe entre as vizinhas"
        return Resultado(Decisao.REVISAR, escolhido.no_id, motivo)
    if limiar is None or escolhido.pontuacao < limiar:
        referencia = "sem limiar calibrado" if limiar is None else f"abaixo do limiar {limiar:.2f}"
        motivo = f"pontuação {escolhido.pontuacao:.2f} {referencia}"
        return Resultado(Decisao.REVISAR, escolhido.no_id, motivo)
    return Resultado(Decisao.PUBLICAR, escolhido.no_id)


def extras(
    arvore: Arvore, central: int, candidatos: Sequence[Pontuado], limiar: float, maximo: int = 2
) -> tuple[int, ...]:
    """Outros Ramos que a Questão também cobre: Candidatos fortes fora do Ramo do central."""
    escolhidos: list[int] = []
    for candidato in sorted(candidatos, key=lambda c: -c.pontuacao):
        if len(escolhidos) == maximo or candidato.pontuacao < limiar:
            break
        if not any(arvore.mesmo_ramo(candidato.no_id, no) for no in (central, *escolhidos)):
            escolhidos.append(candidato.no_id)
    return tuple(escolhidos)
