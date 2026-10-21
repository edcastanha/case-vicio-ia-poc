import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from classificacao.nucleo.dominio.arvore import Arvore
from classificacao.nucleo.dominio.questao import Questao

if TYPE_CHECKING:
    from classificacao.v1.aplicacao.classificar_questao import Classificacao

SCHEMA_DO_VOTO = {
    "type": "object",
    "properties": {
        "no_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "confianca": {"type": "number"},
        "justificativa": {"type": "string"},
        "extras": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["no_id", "confianca", "justificativa", "extras"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Prompt:
    """Instruções de sistema de um papel; o texto de cada versão fica em prompts/v1/<papel>/."""

    papel: str
    versao: str
    texto: str

    @property
    def rotulo(self) -> str:
        """Papel, versão e hash do texto: texto editado sem versão nova não passa despercebido."""
        return f"{self.papel}/{self.versao}@{hashlib.sha256(self.texto.encode()).hexdigest()[:8]}"


@dataclass(frozen=True)
class PromptsDosPapeis:
    classificador: Prompt
    verificador: Prompt
    desempatador: Prompt


class VersoesDePromptMisturadas(ValueError):
    pass


def exigir_versao_unica(classificacoes: Iterable["Classificacao"]) -> list[str]:
    """A calibração vale para uma versão de cada prompt; mudou o prompt, recalibra."""
    sem_versao: list[str] = []
    por_prompt: dict[str, set[str]] = defaultdict(set)
    for c in classificacoes:
        for proposta in (c.classificador, c.verificador, c.desempatador):
            if proposta is None:
                continue
            if not proposta.prompt:
                sem_versao.append(c.questao_id)
            else:
                por_prompt[proposta.prompt.split("/", 1)[0]].add(proposta.prompt)
    problemas = []
    if sem_versao:
        problemas.append(f"votos sem versão de prompt: {', '.join(sorted(set(sem_versao)))}")
    problemas += [
        f"versões misturadas: {', '.join(sorted(rotulos))}"
        for rotulos in por_prompt.values()
        if len(rotulos) > 1
    ]
    if problemas:
        raise VersoesDePromptMisturadas("; ".join(problemas))
    return sorted(rotulo for rotulos in por_prompt.values() for rotulo in rotulos)


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
