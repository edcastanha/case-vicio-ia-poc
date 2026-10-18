# Relatório — classificação de tópicos

## a) Como pensei

**O problema real não é classificar, é saber quando a classificação é confiável.** Um modelo de linguagem acerta a maioria das questões; o que a régua cobra é que, entre as publicadas, 95% estejam certas — e que eu diga antes quanto vou acertar. Então o desenho começou pela pergunta "que sinal, observável sem gabarito, separa acerto de erro?", e não pela escolha do modelo.

**Hipótese central: dois modelos de famílias diferentes concordando é um sinal forte e barato.** Modelos diferentes, com entradas diferentes, erram de jeitos diferentes; quando concordam, é mais provável que estejam certos. Por isso: o Classificador vê a classificação de origem (útil, mas às vezes errada); o Verificador não vê nem a origem nem o Classificador. Um terceiro modelo, o Juiz, só entra no desacordo, e só para escolher a sugestão que vai ao professor — nunca para publicar, porque desacordo é exatamente o sinal de questão difícil.

**Usar a régua a favor, sem trapacear.** A régua aceita como certo o nó do gabarito, o pai ou o filho. Quando os dois modelos escolhem subtemas irmãos, publico no tema pai: ele está certo se o gabarito for qualquer um dos dois. Publicar na disciplina (o "pai do pai") seria o mesmo atalho levado ao extremo — e recriaria a lixeira que o case critica; descartei.

**A previsão de precisão vem de uma amostra rotulada, não da confiança do modelo.** Sorteei 50 questões, 80% delas entre as que poderiam ser publicadas, para estimar sem viés a precisão de quem publica. Não tive acesso a um advogado ou professor de Direito para rotular, então rotulei as 50 com um agente de IA especializado (GPT 5.6 Terra), de outra família que os modelos do pipeline, com uma skill para questões jurídicas, e registrei a justificativa de cada escolha na planilha. Nas 40 em que Classificador e Verificador concordaram, o Nó do pipeline ficou no Ramo do rótulo em todas. Nas 10 de desacordo, que nunca são publicadas, ficou em 7. Um terceiro modelo, o Rotulador (Opus), respondeu às cegas como segunda opinião e caiu no Ramo do rótulo em 46 de 50. As limitações estão declaradas: o gabarito da calibração é de um modelo, não de um especialista, e os rótulos saíram da lista de candidatos da planilha, que sempre contém os Nós votados. As duas coisas podem deixar a previsão otimista (ADR 0006). Em produção, a auditoria amostral do Professor substitui esta amostra por uma humana.

**Becos sem saída e correções de rota:**

- **Infraestrutura (descartada para o case).** Comecei planejando RabbitMQ com DLQ e um banco vetorial/grafo. Para 359 questões isso consome o tempo que deveria ir para calibração. Fiquei com fila e DLQ em arquivo, retomáveis, e levei o desenho com mensageria para a seção de produção (ADR 0001).
- **Agente + crítico auditor (descartado).** Um crítico que lê a resposta do primeiro agente tende a concordar com ela (ancoragem); a aprovação dele deixaria de ser um sinal independente e a previsão ficaria otimista. Aproveitei só a ideia boa — perguntar "esse tema não é genérico demais?" — como instrução nos três prompts.
- **Calibração ingênua (corrigida).** Escolher o limiar na amostra rotulada e medir a precisão nela mesma infla o número. Num teste com pontuação sem informação nenhuma, a conta ingênua dizia 100% de precisão; o bootstrap do procedimento inteiro (recalibrar em reamostras e medir fora delas) estimou 77%, perto dos 80% reais. A previsão entregue usa o bootstrap.
- **Concordância que não informa (corrigida).** No piloto, questões que misturam cinco assuntos tiveram os dois modelos concordando… com confiança declarada de 0,2. Passou a valer: se um dos modelos se declara em dúvida, não publica.
- **Mesmo modelo nos dois papéis (corrigido).** Com só uma chave de API, testei Classificador e Verificador no mesmo modelo: na Q0328 vieram o mesmo nó, a mesma confiança e quase a mesma justificativa. Era o modelo concordando consigo mesmo. Daí em diante, os papéis ficaram com famílias diferentes: Claude no Classificador e DeepSeek no Verificador. O Gemini no Verificador parou na 29ª Questão pela cota gratuita, e misturar dois Verificadores numa rodada faria a calibração medir dois sistemas. Ele ficou só nos embeddings.
- **Prompts sem versão (corrigido).** Os prompts nasceram como constantes no código, e nada dizia qual texto gerou cada voto. Como a previsão vale para um par (modelo, prompt), cada papel ganhou um prompt versionado em arquivo, cada voto grava a versão, e a calibração recusa rodadas com versões misturadas. Refazer as 359 pelo cache reproduziu todas as classificações sem nenhuma chamada (ADR 0003).
- **Texto que o aluno não vê chegava ao modelo (corrigido).** Auditando as entradas, achei na Q0099 cerca de 700 caracteres de metadados e CSS do Word em cada alternativa, restos de comentários condicionais que a limpeza antiga não tirava. Era lixo, mas é exatamente por onde uma instrução escondida passaria. A limpeza passou a manter só o texto visível, e uma Questão cujo texto fala com o modelo ("ignore as instruções", "classifique no nó", `no_id`) vai para Revisar sem passar por nenhum modelo. Nenhuma das 359 dispara (ADR 0005).
- **Números mais confiantes que a amostra (corrigidos).** A primeira entrega previu precisão 1,00 com intervalo 1,00–1,00, porque os 34 rótulos da calibração estavam todos certos e o bootstrap só reamostra o que existe. Agora o ponto é o menor entre o bootstrap e a suavização de Laplace, (34+1)/(34+2) = 0,97, e o intervalo inclui o de Wilson para 34 de 34, que começa em 0,90 (ADR 0002). A mesma regra corrigiu a coluna `confianca`, que valia 1,00 em todas as linhas, até em Revisar e Fora. Agora ela é a taxa suavizada de cada grupo na Amostra: 0,97 em Publicar, 0,67 nos desacordos (a sugestão acertou 7 de 10), 0,83 em Tema duplicado, 0,75 com dúvida declarada e 0,50 em Fora, que não tem nenhuma na Amostra. E o teto da cobertura era 0,82 porque contava as 46 Questões de Tema duplicado ou com dúvida, que nunca publicam. O intervalo agora vai de 0,54 a 0,69.

## b) Diagnóstico: o que atrapalha classificar certo

**Na árvore de temas**

1. **Oito temas duplicados entre disciplinas** (lista no memo). Achei no piloto: na Q0112, um modelo escolheu "Penal > Organizações Criminosas" e o outro "Legislação Especial > Organizações Criminosas". Cada lado é um ramo diferente, e dois classificadores, humanos ou máquinas, podem acertar o assunto e errar o tema. Nenhuma questão nesses temas é publicada até a convenção ficar clara.
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

**Os números da rodada.** As 359 foram classificadas, sem nenhuma falha que sobrasse. Houve Concordância de Ramo em 295 (82%): 255 no mesmo Nó e 40 em Nós do mesmo Ramo. Houve 61 desacordos (17%), e em 3 os dois modelos disseram que nenhum Nó servia.

| Decisão | Questões | Por quê |
|---|---|---|
| Publicar | 249 (69%) | Concordância, fora de Tema duplicado, sem dúvida declarada e acima do limiar calibrado (0,55) |
| Revisar | 107 (30%) | 61 desacordos, 36 Temas duplicados, 10 com um modelo em dúvida |
| Fora | 3 (1%) | os dois modelos: nenhum Nó serve |

Nenhuma Questão foi barrada só pelo limiar: as regras de Ramo, de Tema duplicado e de dúvida declarada já tiram as arriscadas. A previsão é **precisão de 0,97 (de 0,90 a 1,00) e cobertura de 0,69 (de 0,54 a 0,69)**. O intervalo de precisão é largo de propósito: 34 acertos em 34 não provam 95% com 95% de confiança. A cobertura não passa de 0,69 porque um limiar mais baixo não publicaria mais nada, e um mais alto, como alguns que o bootstrap escolheu, publicaria menos.

**O que os rótulos mostraram.** Das 50 Questões da amostra, 8 têm o rótulo num Tema duplicado, e isso confirma a regra de não publicar ali. Nos 10 desacordos da amostra, o Juiz ficou no Ramo do rótulo em 6, o Classificador em 4 e o Verificador em 6. A sugestão que chega ao Professor, que é a do Juiz ou, sem ela, a do primeiro voto válido, acertou em 7. O Juiz ajuda a sugerir, mas não é um desempate confiável: é por isso que ele nunca publica.

## c) Produção: 50 mil questões por semana

**Custo medido.** A DeepSeek (Verificador e Juiz) custou US$ 3,04 em 439 requisições, testes incluídos: no máximo US$ 0,0085 por Questão, ou cerca de US$ 425 por semana para 50 mil Questões. O Classificador saiu da assinatura do Claude Code, mas pelo custo equivalente que o `claude -p` informa (US$ 0,19 por Questão no piloto) ele custaria cerca de US$ 9.700 por semana na API: mais de 95% do total. Cada requisição leva ~14,8 mil tokens porque a Árvore inteira vai no prompt. Por isso os dois cortes que mais rendem em produção são os candidatos por embeddings (item 2, abaixo), que tiram a maior parte desses tokens, e o cache de prompt da parte fixa (instruções e Árvore), que é igual em toda chamada.

**Fluxo**

1. **Importação** → normalização (HTML, comando, alternativas) → fila (RabbitMQ ou Redis Streams) com DLQ: uma questão que falha N vezes vai para a DLQ e para a revisão, nunca some.
2. **Candidatos por embeddings**: em vez de mandar a árvore inteira, busca vetorial dos ~15 nós mais próximos. Corta tokens e permite árvores maiores. A árvore inteira continua no prompt quando a busca tem baixa confiança.
3. **Classificador treinado** (barato, sobre embeddings) com os rótulos que o professor já produziu na revisão. Com volume, ele resolve a maior parte; os LLMs ficam para o que ele não tem certeza.
4. **Dois LLMs de famílias diferentes** na faixa de dúvida, com a mesma regra de hoje: publica só com concordância de ramo, sem dúvida declarada, fora de temas duplicados e acima de um limiar calibrado. O Juiz só escolhe a sugestão do professor.
5. **Revisão humana** com fila priorizada por impacto (tópicos mais estudados primeiro) e a sugestão + justificativa do Juiz já na tela. Cada revisão vira rótulo para o classificador treinado e para recalibrar.

**Qualidade contínua**

- **Auditoria amostral semanal**: o professor revisa às cegas uma amostra aleatória das *publicadas* (ex.: 50/semana). É o único número que mede de fato a régua; com ele recalibro o limiar.
- **Reportes de alunos** como sinal: questão reportada sai da publicação e entra na fila; taxa de reporte por tema denuncia lixeiras novas.
- **Deriva**: acompanhar taxa de concordância, de dúvida e de desacordo por tema e por lote de importação; uma queda repentina indica mudança na fonte ou no modelo.
- **Mudou modelo ou prompt → recalibra** na amostra auditada antes de publicar com a configuração nova. Cada voto já grava a versão do prompt (`classificador/v1@hash`), o que permite medir precisão e deriva por versão e reverter trocando a versão ativa.

## O que faria com mais tempo

1. **Gabarito humano e Amostra maior.** O Professor rotularia a Amostra às cegas, e `entrega` refaz a previsão sem mudar código. Mesmo sem nenhum erro, o piso de Wilson só passa de 0,95 com 73 acertos em 73.
2. **A regra dos Temas duplicados**, que libera até 36 Questões (10 pontos de cobertura) sem mudar mais nada.
3. **Prompts v2, candidatos por embeddings e o Gemini como Verificador numa cota paga**, cada um com uma rodada e uma calibração novas (ADR 0003).

## d) Memo ao professor

Em [`memo-professor.md`](memo-professor.md).
