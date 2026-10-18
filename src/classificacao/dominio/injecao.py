"""Indício de injeção: texto da Questão que fala com o modelo em vez de com o aluno.

Os padrões são estreitos de propósito: nenhum dispara nas 359 Questões do case
("assistente de acusação", "ignorar a prova" e "abuso de confiança" são Direito, não instrução).
"""

import re

from classificacao.dominio.questao import Questao

_PADROES = {
    "instrução ao modelo": (
        r"\b(ignore|desconsidere|esqueça|esqueca)\b[^.\n]{0,40}"
        r"\b(instruç|instruc|orientaç|orientac|prompt|regras (acima|anteriores))"
    ),
    "fala com o modelo": (
        r"\b(system prompt|prompt do sistema|modelo de linguagem|llm)\b"
        r"|\b(você|voce) (é|e) (um|uma) (modelo|ia|assistente virtual|chatbot)\b"
    ),
    "ordem de classificar": (
        r"\b(classifique|atribua|retorne|devolva|responda)\b[^.\n]{0,40}"
        r"\b(nó|no_id|tema central|json|extras)\b"
    ),
    "campo do voto": (
        r"\b(no_id|tema_central_id|extras_ids)\b|\"(confianca|justificativa)\"|\{\s*\""
    ),
    "marcador de papel": (
        r"<\|[^|]*\|>|\[/?inst\]|</?(system|assistant|user|questao)>"
        r"|^\s*(system|assistant|user|sistema)\s*:"
        r"|^#{1,6}\s*(origem|questão|questao|sistema|instruç)"
    ),
    "id da árvore": r"\[\d{4}\]",  # o formato em que a Árvore vai no prompt
}
_COMPILADOS = {nome: re.compile(p, re.IGNORECASE | re.MULTILINE) for nome, p in _PADROES.items()}


def indicios_de_injecao(questao: Questao) -> tuple[str, ...]:
    """Um indício por campo e tipo, ex.: "alternativa C: campo do voto"; vazio se nada suspeito."""
    campos = [
        ("enunciado", questao.enunciado),
        ("comando", questao.comando),
        *((f"alternativa {letra}", texto) for letra, texto in questao.alternativas.items()),
        ("origem", f"{questao.disciplina_origem}\n{questao.assunto_origem}"),
    ]
    return tuple(
        f"{campo}: {nome}"
        for campo, texto in campos
        for nome, padrao in _COMPILADOS.items()
        if padrao.search(texto)
    )
