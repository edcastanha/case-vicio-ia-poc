# Relatório — classificação de tópicos

> Rascunho. Trechos marcados «a preencher» dependem da rodada completa e da calibração.

## a) Como pensei

**O problema real não é classificar, é saber quando a classificação é confiável.** Um modelo de linguagem acerta a maioria das questões; o que a régua cobra é que, entre as publicadas, 95% estejam certas — e que eu diga antes quanto vou acertar. Então o desenho começou pela pergunta "que sinal, observável sem gabarito, separa acerto de erro?", e não pela escolha do modelo.

**Hipótese central: dois modelos de famílias diferentes concordando é um sinal forte e barato.** Modelos diferentes, com entradas diferentes, erram de jeitos diferentes; quando concordam, é mais provável que estejam certos. Por isso: o Classificador vê a classificação de origem (útil, mas às vezes errada); o Verificador não vê nem a origem nem o Classificador. Um terceiro modelo, o Juiz, só entra no desacordo, e só para escolher a sugestão que vai ao professor — nunca para publicar, porque desacordo é exatamente o sinal de questão difícil.

**Usar a régua a favor, sem trapacear.** A régua aceita como certo o nó do gabarito, o pai ou o filho. Quando os dois modelos escolhem subtemas irmãos, publico no tema pai: ele está certo se o gabarito for qualquer um dos dois. Publicar na disciplina (o "pai do pai") seria o mesmo atalho levado ao extremo — e recriaria a lixeira que o case critica; descartei.

**A previsão de precisão vem de uma amostra rotulada, não da confiança do modelo.** Sorteei 50 questões, 80% delas entre as que poderiam ser publicadas, para estimar sem viés a precisão de quem publica. Um terceiro modelo, o Rotulador (Opus), respondeu as 50 às cegas, sem ver a origem nem os votos. Onde ele discordou do pipeline (fora do ramo), eu arbitrei entre as duas respostas sem saber qual era de quem. O julgamento humano fica onde muda o resultado. A limitação está declarada: o Rotulador é da mesma família do Classificador, e erros que os dois cometem juntos não chegam até mim, o que pode deixar a previsão otimista (ADR 0004). «a preencher: quantos conflitos, quantas vezes o pipeline venceu a arbitragem»

**Becos sem saída e correções de rota:**

- **Infraestrutura (descartada para o case).** Comecei planejando RabbitMQ com DLQ e um banco vetorial/grafo. Para 359 questões isso consome o tempo que deveria ir para calibração. Fiquei com fila e DLQ em arquivo, retomáveis, e levei o desenho com mensageria para a seção de produção (ADR 0001).
- **Agente + crítico auditor (descartado).** Um crítico que lê a resposta do primeiro agente tende a concordar com ela (ancoragem); a aprovação dele deixaria de ser um sinal independente e a previsão ficaria otimista. Aproveitei só a ideia boa — perguntar "esse tema não é genérico demais?" — como instrução nos três prompts.
- **Calibração ingênua (corrigida).** Escolher o limiar na amostra rotulada e medir a precisão nela mesma infla o número. Num teste com pontuação sem informação nenhuma, a conta ingênua dizia 100% de precisão; o bootstrap do procedimento inteiro (recalibrar em reamostras e medir fora delas) estimou 77%, perto dos 80% reais. A previsão entregue usa o bootstrap.
- **Concordância que não informa (corrigida).** No piloto, questões que misturam cinco assuntos tiveram os dois modelos concordando… com confiança declarada de 0,2. Passou a valer: se um dos modelos se declara em dúvida, não publica.
- **Mesmo modelo nos dois papéis (corrigido).** Com só uma chave de API disponível, testei Classificador e Verificador no mesmo modelo: na Q0328 vieram o mesmo nó, a mesma confiança e quase a mesma justificativa. É o modelo concordando consigo mesmo. A configuração final mantém famílias diferentes (Claude no Classificador, DeepSeek no Verificador).
- **Prompts sem versão (corrigido).** Os prompts nasceram como constantes no código, e nada no resultado dizia qual texto tinha gerado cada voto. Como a previsão de precisão vale para um par (modelo, prompt), passei a versionar o prompt de cada papel em arquivo (`prompts/<papel>/v1.md`), a gravar a versão em cada voto e a recusar calibrar rodadas com versões misturadas. A v1 é o texto que gerou a rodada: refazer as 359 só pelo cache reproduziu todas as classificações sem nenhuma chamada (ADR 0003).
- **Temas duplicados (descoberto no piloto).** Na Q0112 um modelo escolheu "Penal > Organizações Criminosas" e o outro "Legislação Especial > Organizações Criminosas". Ver diagnóstico.

## b) Diagnóstico: o que atrapalha classificar certo

**Na árvore de temas**

1. **Oito temas duplicados entre disciplinas**: Abuso de Autoridade, Crimes contra o meio ambiente, Lavagem de Dinheiro, Lei Maria da Penha, Organizações Criminosas e Tráfico de Drogas existem em Penal *e* em Legislação Especial; Lei de Execução Penal em Legislação Especial *e* Processo Penal; Ação Penal em Penal *e* Processo Penal. Cada lado é um ramo diferente: dois classificadores — humanos ou máquinas — podem acertar o assunto e errar o tema. Nenhuma questão nesses temas é publicada até a convenção ficar clara.
2. **Descrições que não descrevem**: 333 dos 377 temas têm como "descrição" um texto automático ("Subtema de X. 44 questões no source"). Pior que inútil: a contagem empurra um classificador automático justamente para os nós grandes — as lixeiras. Removi essas descrições dos prompts.
3. **Lixeiras previsíveis**: os nós com mais questões no banco de origem são genéricos ou introdutórios — "Sistemas e Princípios Processuais Penais" (538), "Teoria da Pena" (453), "Introdução ao Estudo do Direito Penal" (424). Há 26 nós com título do tipo "introdução / noções gerais / disposições gerais / conceito / princípios".
4. **Granularidade desigual**: 60 temas não têm subtemas, outros têm dezenas; e defeitos de cadastro ("Escolas Crimonológicas", "12 Disposições Gerais…").

**Nas questões**

5. **Classificação de origem não confiável**: 7 questões vêm marcadas com disciplinas fora do recorte (Constitucional, Tributário, Ambiental, Civil), às vezes erradas — a Q0016, "Direito Constitucional", é sobre prisão. 18 vêm sem assunto; 68 têm assuntos fatiados ("Ação Penal (Parte 01)", "(Parte 02)"), que são divisões de apostila, não de matéria.
6. **Formato inconsistente**: HTML cru no enunciado e nas alternativas; 94 questões sem comando; 58 de Certo/Errado, algumas com comando de questão discursiva ("Explique as condições…", Q0008).

**Que questão é difícil, e por quê**

- **Multitemáticas** (várias assertivas, cada uma de um assunto): não existe "o" tema central; qualquer escolha é defensável e o gabarito é uma convenção.
- **Questões cujo contexto não é o assunto**: o enunciado fala de um crime, mas o que decide a resposta é uma regra processual (Q0120: parece "resposta à acusação", decide-se pelo interrogatório, art. 189 do CPP).
- **Fronteira entre disciplinas**: prescrição disciplinar (Administrativo) que usa o prazo penal (Q0113); lei especial que também está na parte especial do CP.
- **Temas duplicados**: o assunto é inequívoco; o *lugar* não é.

«a preencher: números da rodada — % de concordância, desacordos, fora, falhas; o que os rótulos mostraram sobre os temas duplicados e sobre o Juiz»

## c) Produção: 50 mil questões por semana

«a preencher: custo por questão medido na rodada»

**Fluxo**

1. **Importação** → normalização (HTML, comando, alternativas) → fila (RabbitMQ ou Redis Streams) com DLQ: uma questão que falha N vezes vai para a DLQ e para a revisão, nunca some.
2. **Candidatos por embeddings**: em vez de mandar a árvore inteira, busca vetorial dos ~15 nós mais próximos. Corta tokens e permite árvores maiores. A árvore inteira continua no prompt quando a busca tem baixa confiança.
3. **Classificador treinado** (barato, sobre embeddings) com os rótulos que o professor já produziu na revisão. Com volume, ele resolve a maior parte; os LLMs ficam para o que ele não tem certeza.
4. **Dois LLMs de famílias diferentes** na faixa de dúvida, com a mesma regra de hoje: publica só com concordância de ramo, sem dúvida declarada, fora de temas duplicados e acima de um limiar calibrado.
5. **Juiz** só para a sugestão do professor.
6. **Revisão humana** com fila priorizada por impacto (tópicos mais estudados primeiro) e a sugestão + justificativa do Juiz já na tela. Cada revisão vira rótulo para o classificador treinado e para recalibrar.

**Qualidade contínua**

- **Auditoria amostral semanal**: o professor revisa às cegas uma amostra aleatória das *publicadas* (ex.: 50/semana). É o único número que mede de fato a régua; com ele recalibro o limiar.
- **Reportes de alunos** como sinal: questão reportada sai da publicação e entra na fila; taxa de reporte por tema denuncia lixeiras novas.
- **Deriva**: acompanhar taxa de concordância, de dúvida e de desacordo por tema e por lote de importação; uma queda repentina indica mudança na fonte ou no modelo.
- **Mudou modelo ou prompt → recalibra** na amostra auditada antes de publicar com a configuração nova. Cada voto já grava a versão do prompt (`classificador/v1@hash`), o que permite medir precisão e deriva por versão e reverter trocando a versão ativa.

## d) Memo ao professor

Em [`memo-professor.md`](memo-professor.md).
