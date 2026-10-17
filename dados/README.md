# Dados gerados pelo pipeline

Versionados para que a entrega seja auditável e reproduzível sem gastar chamadas a modelos.

| Caminho | O que é |
|---|---|
| `rodada/classificacoes.jsonl` | Votos do Classificador, Verificador e Juiz nas 359 Questões, com a versão do prompt de cada voto (ADR 0003). Insumo da entrega. |
| `rodada/classificacoes.pre-versionamento.jsonl` | O mesmo arquivo antes do versionamento de prompts, com o histórico de tentativas incompletas. |
| `rodada/sinais.json` | Similaridade entre a Questão e o Nó votado, e o Nó mais parecido como reserva (embeddings Gemini). |
| `rodada/resumo.csv` | Leitura humana da rodada: situação (mesmo nó, mesmo ramo, desacordo, fora), caminho do Nó e justificativa. |
| `rodada/falhas-rodada1.jsonl` | DLQ da primeira tentativa da rodada (falhas de provedor depois refeitas). |
| `rotulagem.csv` | Amostra cega de 50 Questões para calibração; a coluna `resposta` é preenchida por `classificacao consolidar` (fonte em `observacao`). |
| `rotulador.json` | Respostas do Rotulador às 50 Questões da amostra, com justificativa e versão do prompt (gerado por `classificacao rotular`; ADR 0004). |
| `arbitragem.csv` | Conflitos entre o Rotulador e o pipeline, com as duas respostas como A/B em ordem sorteada; a coluna `escolha` é preenchida à mão. |
| `falhas-rotulador.jsonl` | DLQ do Rotulador; essas Questões vão para a arbitragem. |
| `arvore-de-temas.csv` | A Árvore de temas em formato legível, para consulta durante a rotulagem. |
| `cache/` | Respostas brutas dos modelos, uma por chave (papel, modelo, prompt, Questão). Com ele, `classificacao rodada` refaz tudo sem chamar nenhum modelo. |
| `piloto/`, `fumaca/`, `fumaca-api/` | Execuções de teste: piloto de 30 Questões e testes de fumaça dos backends. Mantidos como registro do caminho. |
