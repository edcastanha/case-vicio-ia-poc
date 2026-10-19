# Dados gerados pelo pipeline

Versionados para que a entrega seja auditável e reproduzível sem gastar chamadas a modelos.

| Caminho | O que é |
|---|---|
| `rodada/classificacoes.jsonl` | Votos do Classificador, Verificador e Desempatador nas 359 Questões, com a versão do prompt de cada voto (ADR 0003). Insumo da entrega. |
| `rodada/classificacoes.pre-versionamento.jsonl` | O mesmo arquivo antes do versionamento de prompts, com o histórico de tentativas incompletas. |
| `rodada/sinais.json` | Similaridade entre a Questão e o Nó votado, e o Nó mais parecido como reserva (embeddings Gemini). |
| `rodada/resumo.csv` | Leitura humana da rodada: situação (mesmo nó, mesmo ramo, desacordo, fora), caminho do Nó e justificativa. |
| `rodada/falhas-rodada1.jsonl` | DLQ da primeira tentativa da rodada (falhas de provedor depois refeitas). |
| `rotulagem.csv` | Amostra cega de 50 Questões para calibração; a coluna `resposta` foi preenchida por um agente jurídico especializado, com a justificativa em `observacao` (ADR 0006). |
| `rotulador.json` | Respostas do Rotulador às 50 Questões da amostra, com justificativa e versão do prompt (gerado por `classificacao rotular`): segunda opinião às cegas, não fonte de rótulo (ADR 0006). |
| `falhas-rotulador.jsonl` | DLQ do Rotulador (falhas de provedor). |
| `arvore-de-temas.csv` | A Árvore de temas em formato legível, para consulta durante a rotulagem. |
| `cache/` | Respostas brutas dos modelos, uma por chave (papel, modelo, prompt, Questão). Com ele, `classificacao rodada` refaz tudo sem chamar nenhum modelo. |
| `piloto/`, `fumaca/`, `fumaca-api/` | Execuções de teste: piloto de 30 Questões e testes de fumaça dos backends. Mantidos como registro do caminho. |
