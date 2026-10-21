from classificacao.nucleo.dominio.questao import Questao


def texto_da_questao(questao: Questao) -> str:
    """O texto que o aluno lê: enunciado, comando e alternativas. A Origem fica de fora:
    ela entra no Ranqueador como sinal próprio, para ele aprender quanto confiar nela."""
    alternativas = [f"{letra}) {texto}" for letra, texto in sorted(questao.alternativas.items())]
    return "\n".join([questao.enunciado, questao.comando, *alternativas]).strip()
