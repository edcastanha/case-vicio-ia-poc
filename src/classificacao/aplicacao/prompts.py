from classificacao.dominio.arvore import Arvore
from classificacao.dominio.questao import Questao

SCHEMA_DO_VOTO = {
    "type": "object",
    "properties": {
        "no_id": {"type": ["integer", "null"]},
        "confianca": {"type": "number"},
        "justificativa": {"type": "string"},
        "extras": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["no_id", "confianca", "justificativa", "extras"],
    "additionalProperties": False,
}

_REGRAS_COMUNS = """\
Regras da árvore:
- Escolha um Tema ou um Subtema pelo número entre colchetes. Nunca uma Disciplina, e nunca um \
número que não esteja na lista.
- Prefira o Subtema mais específico que cubra o assunto central. Se a questão cobre vários \
Subtemas do mesmo Tema por igual, escolha o Tema.
- Cuidado com nós genéricos ou introdutórios (noções gerais, introdução, conceito, princípios, \
disposições gerais). Eles atraem questões que não são deles. Só os escolha se a questão for de \
fato sobre a noção geral; antes, procure um nó específico que trate do instituto cobrado.
- Se nenhum nó da árvore serve (por exemplo, a questão é de outra disciplina), devolva no_id null.

Campos da resposta:
- no_id: o número do nó, ou null.
- confianca: de 0 a 1, a chance de um professor especialista concordar com a sua escolha. \
Seja calibrado: 0.9 deve significar que você erraria cerca de 1 em 10 escolhas assim.
- justificativa: 1 a 3 frases, citando o instituto ou dispositivo legal que decide a questão.
- extras: até 3 outros nós que a questão também cobre de forma substancial; \
lista vazia se não houver.
"""

SISTEMA_CLASSIFICADOR = (
    """\
Você classifica questões de concurso de Direito Penal, Processo Penal, Legislação Penal Especial \
e Criminologia numa árvore de temas. O aluno estuda por tema: se a questão ficar no tema errado, \
ele estuda a matéria errada.

Pergunte-se: qual é o assunto central desta questão? Leia o enunciado e as alternativas inteiros; \
o assunto central é o que diferencia a alternativa certa das erradas, não apenas o contexto citado \
no enunciado. A origem informada (como o site de origem classificou) é só uma pista e pode estar \
errada.

"""
    + _REGRAS_COMUNS
)

SISTEMA_VERIFICADOR = (
    """\
Você é professor de cursinho para concursos da área criminal e organiza um banco de questões por \
tema para os seus alunos.

Para esta questão, identifique primeiro qual instituto jurídico o aluno precisa dominar para \
acertá-la (por exemplo, um crime específico, uma regra processual, uma teoria). Depois localize \
esse instituto na árvore de temas.

"""
    + _REGRAS_COMUNS
)

SISTEMA_JUIZ = (
    """\
Dois classificadores independentes discordaram sobre em que nó da árvore de temas uma questão de \
concurso deve ficar. Você recebe a questão, a árvore e as duas propostas com as justificativas.

Decida qual nó é o correto para o assunto central da questão. Pode escolher uma das propostas ou, \
se ambas estiverem erradas, outro nó da árvore. Na justificativa, explique em linguagem simples, \
para um professor de Direito, por que a proposta descartada está errada.

"""
    + _REGRAS_COMUNS
)


def arvore_para_prompt(arvore: Arvore) -> str:
    nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.caminho)
    return "\n".join(f"[{no.id}] {no.caminho}" for no in nos)


def sistema_com_arvore(sistema: str, arvore: Arvore) -> str:
    """Instruções + árvore: igual em toda chamada do papel, prefixo estável para o cache."""
    return f"{sistema}\n## Árvore de temas\n\n{arvore_para_prompt(arvore)}"


def questao_para_prompt(questao: Questao, com_origem: bool) -> str:
    alternativas = "\n".join(f"{letra}) {texto}" for letra, texto in questao.alternativas.items())
    partes = [
        "## Questão",
        questao.enunciado,
        questao.comando,
        alternativas,
    ]
    if com_origem:
        partes += [
            "## Origem (classificação do site de origem; pode estar errada)",
            f"{questao.disciplina_origem} > {questao.assunto_origem}",
        ]
    return "\n\n".join(partes)


def disputa_para_prompt(questao: Questao, proposta_a, proposta_b) -> str:
    return "\n".join(
        [
            questao_para_prompt(questao, com_origem=False),
            f"Proposta A: {proposta_a.no_id} — {proposta_a.justificativa}",
            f"Proposta B: {proposta_b.no_id} — {proposta_b.justificativa}",
        ]
    )
