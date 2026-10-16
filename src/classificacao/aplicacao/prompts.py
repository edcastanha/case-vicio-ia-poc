from classificacao.dominio.arvore import Arvore
from classificacao.dominio.questao import Questao

SCHEMA_DO_VOTO = {
    "type": "object",
    "properties": {
        "no_id": {"type": ["integer", "null"]},
        "confianca": {"type": "number", "minimum": 0, "maximum": 1},
        "justificativa": {"type": "string"},
        "extras": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["no_id", "confianca", "justificativa", "extras"],
}

SISTEMA_CLASSIFICADOR = "Classifique a questão de concurso em um nó da árvore de temas."
SISTEMA_VERIFICADOR = "Classifique a questão de concurso em um nó da árvore de temas."
SISTEMA_JUIZ = "Escolha qual das duas classificações propostas está correta."


def arvore_para_prompt(arvore: Arvore) -> str:
    nos = sorted(arvore.nos_que_podem_receber_questao(), key=lambda no: no.caminho)
    return "\n".join(f"[{no.id}] {no.caminho}" for no in nos)


def questao_para_prompt(questao: Questao, arvore: Arvore, com_origem: bool) -> str:
    alternativas = "\n".join(f"{letra}) {texto}" for letra, texto in questao.alternativas.items())
    partes = [
        "## Árvore de temas",
        arvore_para_prompt(arvore),
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


def disputa_para_prompt(questao: Questao, arvore: Arvore, proposta_a, proposta_b) -> str:
    return "\n".join(
        [
            questao_para_prompt(questao, arvore, com_origem=False),
            f"Proposta A: {proposta_a.no_id} — {proposta_a.justificativa}",
            f"Proposta B: {proposta_b.no_id} — {proposta_b.justificativa}",
        ]
    )
