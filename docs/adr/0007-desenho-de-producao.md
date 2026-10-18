# Em produção, o voto caro sai do caminho e a regra de publicação continua a mesma

Para 50 mil Questões por semana, a regra do ADR 0002 não muda: só publica quem tem dois votos independentes, de famílias diferentes, concordando no mesmo Ramo, sem dúvida declarada, fora de Tema duplicado e acima do limiar calibrado. O que muda é quem dá os votos e quanto texto vai em cada chamada.

## As etapas

| Etapa | Tipo de IA | Quando entra |
|---|---|---|
| 1. Importação | nenhuma: `limpar_html` e Indício de injeção (ADR 0005) | toda Questão |
| 2. Candidatos | embeddings: os ~15 Nós mais próximos da Questão | toda Questão |
| 3. Primeiro voto | Classificador treinado, sobre os mesmos embeddings | quando houver rótulos do Professor bastantes para calibrá-lo; antes disso, o Classificador (LLM) |
| 4. Segundo voto | LLM de outra família (hoje o Verificador, DeepSeek) | toda Questão |
| 5. Desempate | o Classificador (Claude) e, se ainda houver desacordo, o Juiz, que só sugere | só no desacordo entre os votos 3 e 4 |
| 6. Revisão | o Professor | toda Questão em Revisar |

O **Classificador treinado conta como um dos dois votos independentes.** Ele aprende só com as revisões do Professor e não vê o voto do LLM, então o erro dele não é o erro do LLM. Se os votos 3 e 4 concordam, vale a regra do ADR 0002. Se discordam, a Questão volta ao par do case, Classificador e Verificador, e publica só se esses dois concordarem. Ele entra como primeiro voto depois de ter a própria calibração na auditoria (ver Qualidade), nunca antes.

**Agentes ficam fora do caminho da decisão.** Um agente que revisa a resposta de outro ancora nela, e foi por isso que o crítico auditor foi descartado no case. Eles servem onde não publicam: montar para o Professor o dossiê de cada Questão da fila (sugestão, justificativa e artigos citados), agrupar os reportes de alunos por causa e rascunhar descrições de Temas para o Professor aprovar.

## Custo por Questão

A base é o que o case mediu: US$ 0,0069 por requisição DeepSeek e US$ 0,19 por Questão no Classificador (o custo equivalente que o `claude -p` informou no piloto, um teto para a API). A Árvore é 92% do texto de entrada de cada chamada; com 15 candidatos, a entrada cai cerca de 8 vezes. A conta assume chamadas 5 vezes mais baratas, porque a saída (o voto e a justificativa) não encolhe.

| | Por Questão | Por semana (50 mil) |
|---|---|---|
| Hoje, como no case | US$ 0,20 | ~US$ 10.200 |
| Fase 1: candidatos por embeddings | US$ 0,041 | ~US$ 2.000 |
| Fase 2: Classificador treinado como primeiro voto | US$ 0,009 | ~US$ 440 |

Na Fase 2, o Classificador (LLM) só entra nos ~18% de desacordo, a taxa de desacordo e Fora de hoje. As premissas a medir no piloto de produção são o fator 5, a taxa de desacordo do Classificador treinado e o preço pago dos embeddings (~US$ 0,0002 por Questão).

## O gargalo é o Professor

Com as taxas do case, 30% de 50 mil são cerca de 15 mil Questões por semana em Revisar. Isso pesa mais que o custo dos modelos. Há três alavancas:
- a regra dos Temas duplicados, que tira cerca de 10 pontos da fila;
- a fila priorizada pelos Temas mais estudados;
- cada revisão virar rótulo do Classificador treinado.

O que não for revisado fica fora do aluno. A fila nunca é esvaziada publicando.

## Encaixe no fluxo

As Questões importadas passam pelas etapas 1 a 5 e saem em Publicar, na fila do Professor ou em Fora. Cada revisão vira rótulo, e toda semana o Classificador treinado é retreinado e o limiar é recalibrado. Um reporte de aluno tira a Questão da publicação na hora e a põe na fila.

## Qualidade contínua, com gatilhos

- **Auditoria:** toda semana, o Professor confere às cegas 50 publicadas sorteadas. Com 3 erros ou mais (abaixo de 95%), a publicação automática para até a recalibração. A Precisão é estimada nas últimas 4 semanas, 200 Questões.
- **Reportes:** um Tema com o dobro da taxa mediana de reporte passa a só Revisar até o Professor olhar. É assim que uma Lixeira nova aparece.
- **Deriva:** se num lote de importação a Concordância ou a dúvida declarada muda mais de 5 pontos contra as 4 semanas anteriores, o lote vai para Revisar.
- **Mudou modelo ou prompt:** a calibração é refeita antes de publicar (ADR 0003). Cada voto já grava a versão do prompt.

## Considered Options

- **O Classificador treinado publica sozinho quando está confiante:** descartado. É um voto só, e a Precisão dele seria medida contra os mesmos rótulos com que foi treinado.
- **Dois LLMs sempre, só com candidatos:** é a Fase 1. Vale enquanto não há rótulos para treinar, mas custa quase 5 vezes a Fase 2.
- **Agente que decide e se corrige:** descartado pela ancoragem, como o crítico auditor do case.
