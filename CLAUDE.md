# case-vicio-ia-poc

Case de seleção da Vício: classificar 359 questões penais na árvore de temas e decidir Publicar / Revisar / Fora sob a Régua (≥95% de precisão nas publicadas). Enunciado em `case-ia-classificacao-de-topicos.pdf`, dados em `anexos-case-ia.zip`. Prazo: 18/10/2026.

## Antes de mexer no código

- Leia `GLOSSARY.md` e use exatamente esses termos no código, nos testes e nos textos (Questão, Nó, Tema, Subtema, Ramo, Classificador, Verificador, Juiz, Professor…). Termo novo ou ambíguo → resolva e atualize o glossário.
- Leia `docs/adr/`. Não reverta uma decisão registrada sem falar com o usuário.

## Convenções

- Clean Architecture em `src/classificacao/`: `dominio/` (sem I/O, só depende de si), `aplicacao/` (casos de uso + portas), `adaptadores/` (provedores, `claude -p`, arquivos, cache, DLQ), `entrada/` (CLI). Dependências apontam para dentro.
- Nomes do domínio e dos casos de uso em português sem acento, iguais ao glossário (`Questao`, `Ramo`, `Decisao.PUBLICAR`).
- Testes com `pytest`: `tests/unit/` usa fakes e nunca chama rede nem `claude -p`; `tests/contrato/` usa respostas gravadas. Regras do domínio (Ramo, Régua, decisão, calibração) são feitas em TDD.
- Lint e formatação com `ruff`.
- Backend por papel via `.env` (`api` ou `claude-code`); chaves só em `.env`, nunca versionado. Chamadas reais (API ou `claude -p`) respeitam os limites do plano do usuário: piloto de 30 questões, no máximo 2 chamadas paralelas em `claude-code`, rodada completa só com autorização.
- Trabalho na branch `develop`.
