# Relatório — classificação de tópicos

> **Em resumo.** Das 359 questões, **249 (69%) vão direto ao aluno**, 107 vão para o Professor com uma sugestão e 3 não cabem em nenhum tema. Prevejo que **97 em cada 100 publicadas estejam certas** (entre 90 e 100). Só publico quando dois modelos de empresas diferentes, sem ver um ao outro, escolhem o mesmo ramo da árvore.

## a) Como pensei

Um modelo de linguagem acerta a maioria das questões. O difícil é saber, sem gabarito, **quais** ele acertou, porque a Régua cobra 95% de acerto nas publicadas e uma previsão feita antes do resultado. Por isso comecei pela pergunta "que sinal separa acerto de erro?", e não pela escolha do modelo. Cheguei a três decisões:

1. **Dois modelos de famílias diferentes precisam concordar.** Modelos diferentes, com informações diferentes, erram de jeitos diferentes. O Classificador (Claude) vê a classificação de origem da questão. O Verificador (DeepSeek) não vê a origem nem a resposta do Classificador. Quando os dois discordam, um terceiro modelo, o Desempatador, escolhe a sugestão que vai para o Professor, mas nunca publica: o desacordo é justamente o sinal de questão difícil.
2. **Subtemas irmãos sobem para o tema pai.** A Régua aceita o tema certo, o pai ou o filho. Se um modelo escolhe um subtema e o outro escolhe o irmão, publico no tema pai, que está certo nos dois casos. Subir até a disciplina seria o mesmo atalho levado ao extremo, e recriaria a lixeira que o case critica.
3. **A previsão vem de uma amostra conferida, não da confiança que o modelo declara.** Sorteei 50 questões e as rotulei com um agente de IA especializado em Direito (GPT 5.6 Terra, de outra empresa), que justificou cada escolha. Não tive um especialista humano (ADR 0006). Nas 40 em que os dois modelos concordaram, todas estavam no ramo do rótulo. Nas 10 de desacordo, a sugestão acertou 7. Há duas limitações, ambas declaradas, e as duas deixam a previsão otimista: o gabarito é de um modelo, e o rótulo foi escolhido numa lista que sempre continha os temas votados.

**O que testei e mudei no caminho**

| Tentativa | O que aconteceu | O que ficou |
|---|---|---|
| RabbitMQ e banco vetorial | Tempo demais para 359 questões | Fila em arquivo; a mensageria foi para a produção (ADR 0001) |
| Um agente crítico revisando o primeiro | O crítico concorda com o que lê (ancoragem) | Só a pergunta "o tema não é genérico demais?" nos prompts |
| O mesmo modelo nos dois papéis | Na Q0328: mesmo tema, mesma confiança, mesma justificativa | Sempre duas famílias diferentes |
| Gemini como Verificador | A cota gratuita parou na 29ª questão | DeepSeek na rodada inteira; Gemini só nos embeddings |
| Publicar com concordância, mesmo com dúvida | Os modelos concordavam com confiança 0,2 em questões de cinco assuntos | Dúvida declarada vai para Revisar |
| Calibrar e medir na mesma amostra | Num teste sem nenhum sinal, a conta dava 100%; o real era 80% | Reamostrar: calibrar numa parte e medir na outra (deu 77%) |
| Prompts escritos dentro do código | Não dava para saber que texto gerou cada voto | Prompts versionados, com a versão gravada em cada voto (ADR 0003) |
| A limpeza antiga do HTML | A Q0099 mandava ao modelo ~700 caracteres de CSS do Word | Só o texto visível; texto que dá ordens ao modelo vai para Revisar (ADR 0005) |
| Previsão só pela reamostragem | Deu 1,00 sem margem, porque a amostra não tinha nenhum erro | 34 acertos em 34 viram 0,97, de 0,90 a 1,00; a mesma regra corrigiu a confiança e a cobertura (ADR 0002) |

## b) Diagnóstico: o que atrapalha classificar certo

**Na árvore de temas**

- **Oito temas existem em duas disciplinas**, como Lei Maria da Penha em Penal e em Legislação Especial (lista no memo). O assunto é claro, o lado é que não é: na Q0112, um modelo escolheu "Penal > Organizações Criminosas" e o outro, "Legislação Especial > Organizações Criminosas". Não publico nesses temas, e há 36 questões paradas por isso.
- **As descrições não descrevem.** 333 dos 377 temas têm um texto automático, como "Subtema de X. 44 questões no source". Pior: a contagem empurra a máquina para os temas grandes, que são as lixeiras. Tirei essas descrições dos prompts.
- **As lixeiras são previsíveis.** Os temas com mais questões são os genéricos: "Sistemas e Princípios Processuais Penais" (538), "Teoria da Pena" (453) e "Introdução ao Estudo do Direito Penal" (424). Há 26 temas com títulos como "introdução", "noções gerais" ou "disposições gerais".
- **Há desníveis e erros de cadastro.** 60 temas não têm subtemas, outros têm dezenas, e há erros como "Escolas Crimonológicas".

**Nas questões**

- **A classificação de origem não é confiável.** 7 questões vêm de disciplinas fora do recorte, às vezes erradas (a Q0016 está em "Direito Constitucional", mas é sobre prisão). 18 vêm sem assunto, e 68 vêm com assuntos fatiados como apostila, por exemplo "Ação Penal (Parte 01)".
- **O formato é inconsistente.** O texto vem em HTML cru, 94 questões não têm comando, e algumas de Certo/Errado têm comando de questão discursiva (Q0008).

**Que questão é difícil, e por quê**

- **Multitemáticas:** cada assertiva trata de um assunto, e não existe "o" tema central.
- **Contexto diferente do assunto:** o enunciado fala de um crime, mas a resposta depende de uma regra processual. Na Q0120, parece "resposta à acusação", mas o que decide é o interrogatório.
- **Fronteira entre disciplinas:** a Q0113 é prescrição disciplinar, de Direito Administrativo, mas usa o prazo penal.

**Os números**

| Decisão | Questões | Por quê |
|---|---|---|
| Publicar | 249 (69%) | Os dois modelos no mesmo ramo, sem tema duplicado e sem dúvida declarada |
| Revisar | 107 (30%) | 61 desacordos, 36 temas duplicados e 10 com um modelo em dúvida |
| Fora | 3 (1%) | Os dois modelos disseram que nenhum tema serve |

Os modelos concordaram em 295 questões: 255 no mesmo tema e 40 em temas do mesmo ramo. **A previsão é de 0,97 de precisão (de 0,90 a 1,00) e 0,69 de cobertura (de 0,54 a 0,69).** O intervalo de precisão é largo de propósito, porque 34 acertos em 34 não bastam para garantir 95%. A cobertura não passa de 0,69 porque nenhuma questão foi barrada só pelo limiar de confiança. Nos 10 desacordos da amostra, o Desempatador acertou o ramo em 6, e é por isso que ele só sugere.

## c) Produção: 50 mil questões por semana

A regra de publicação continua a mesma: dois votos independentes, de famílias diferentes, no mesmo ramo. O que muda é **quem vota** e **quanto texto vai em cada chamada** (ADR 0007).

| Etapa | Tipo de IA | Quando entra | Custo por questão |
|---|---|---|---|
| 1. Importação | Nenhuma: limpeza do HTML e indício de injeção | Sempre | ~0 |
| 2. Candidatos | Embeddings escolhem os ~15 temas mais próximos | Sempre | ~US$ 0,0002 |
| 3. Primeiro voto | Classificador treinado com as revisões do Professor (até haver rótulos, o LLM Classificador) | Sempre | ~0 |
| 4. Segundo voto | LLM de outra família (DeepSeek) | Sempre | US$ 0,0014 |
| 5. Desempate | Claude; o Desempatador só sugere | No desacordo, ~18% | US$ 0,040 |
| 6. Revisão | O Professor | Em Revisar | Tempo dele |

**Custo.** Hoje, cada chamada leva a árvore inteira, que é 92% do texto. Com 15 candidatos no lugar dela, assumo chamadas 5 vezes mais baratas.

| | Por questão | Por semana |
|---|---|---|
| Hoje, medido no case | US$ 0,20 | ~US$ 10.200 |
| Com candidatos | US$ 0,041 | ~US$ 2.000 |
| Com o Classificador treinado como primeiro voto | US$ 0,009 | ~US$ 440 |

O fator 5 e os 18% de desacordo são premissas a medir no piloto.

**O gargalo é o Professor, não o custo.** Com as taxas de hoje, seriam cerca de 15 mil questões por semana em Revisar. Para reduzir a fila, há três caminhos:

- a regra dos temas duplicados, que tira 10 pontos da fila;
- a fila ordenada pelos temas mais estudados;
- cada revisão virar exemplo para o Classificador treinado.

O que não for revisado não chega ao aluno.

**Agentes não decidem.** Pelo mesmo motivo do crítico descartado na seção a), os agentes não decidem. Eles preparam o trabalho do Professor: montam o dossiê de cada questão da fila, agrupam os reportes de alunos e rascunham descrições de temas.

**O fluxo de cada semana.** As questões importadas passam pelas etapas 1 a 5. As revisões da semana retreinam o primeiro voto e recalibram o limiar. Um reporte de aluno tira a questão do ar na hora e a põe na fila.

**Qualidade contínua, com gatilhos**

- **Auditoria:** o Professor confere, às cegas, 50 publicadas sorteadas por semana. Com 3 erros ou mais, a publicação automática para até recalibrar.
- **Reportes:** um tema com o dobro da taxa normal de reportes passa a ir só para Revisar. É assim que uma lixeira nova aparece.
- **Mudanças:** um lote em que a concordância muda mais de 5 pontos vai para Revisar. Trocou de modelo ou de prompt, a calibração é refeita antes de publicar (ADR 0003).

## O que faria com mais tempo

1. **Trocar o gabarito da amostra por um humano** e aumentar a amostra. Mesmo sem nenhum erro, só com 73 acertos em 73 dá para garantir 95%.
2. **Aplicar a regra dos temas duplicados**: até 36 questões a mais, ou 10 pontos de cobertura.
3. **Testar prompts novos e o Gemini como Verificador** numa cota paga, cada um com rodada e calibração novas.

## d) Memo ao professor

Em [`memo-professor.md`](memo-professor.md).
