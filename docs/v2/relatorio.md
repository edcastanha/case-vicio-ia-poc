# Relatório v2: um sistema de classificação sem modelo de linguagem na decisão

> **Em resumo.** 125 das 559 Questões avaliadas (22%) vão direto ao aluno. Prevejo que 97 em cada 100 delas estejam certas (intervalo de 0,76 a 1,00). Quem decide é um Ranqueador treinado nas 100 Questões da equipe. Nenhum modelo de linguagem escolhe, vota ou valida o Tema, e `uv run classificacao v2 entrega` regenera os dois arquivos em cerca de um minuto, na CPU, sem rede, com saída idêntica a cada rodada.

## a) O sistema, peça por peça

O difícil não é achar um Tema provável: é saber **quando o sistema pode confiar em si mesmo**. Cada peça gera um sinal que ajuda a separar acerto de erro, e a decisão é de um modelo pequeno, calibrado nos exemplos da equipe.

| Peça | O que faz | Por que está ali |
|---|---|---|
| Limpeza do texto | Mantém só o que o aluno lê | Vem da v1; o lixo do HTML distorce qualquer sinal |
| Temas enriquecidos | `claude -p` descreveu os 371 Nós (o que entra, o que não entra, termos, leis) **vendo só a Árvore**, com prompt versionado; numa amostra de 30, um segundo modelo propôs 22 correções, revisadas e aceitas pelo autor, e um teste confere contra a Árvore todo caminho citado | 333 temas tinham descrição automática ("44 questões no source") |
| Embeddings locais | Vetores das Questões e dos Temas, gerados uma vez na CPU e versionados | Similaridade de assunto, sem custo nem cota |
| Leis citadas | Número ou apelido, com um dicionário de 29 leis | A lei diz o assunto; certa em 9 de 13 exemplos |
| Origem → Nó | O assunto do site casado com o título de um Nó | Sinal fraco: certo em 22 de 92 exemplos |
| Vizinhas | As 5 Questões rotuladas mais parecidas votam pela Régua | Ensinam a **convenção da equipe** |
| Candidatos | Top-10 por similaridade, mais leis, Origem, vizinhas e o pai de cada Subtema | O Gabarito está entre eles em 90 de 92 exemplos |
| Ranqueador por Ramo | Regressão logística com 11 sinais estima a chance de cada Candidato **ser o Gabarito**; cada Nó é pontuado pela soma das chances do seu Ramo | Pela Régua, o Tema pai acerta qualquer Subtema; a dúvida entre irmãos sobe para ele sem regra especial |
| Decisão | Publica acima do limiar; Tema duplicado só com exemplo da equipe; Direito Penal Militar é Fora | Regras curtas e testadas |

**O que testei e descartei.** A métrica é a da Régua: publicadas e acertos fora do fold no limiar de maior cobertura com taxa suavizada ≥ 0,96.

| Ranqueador | bge-m3: top-1 | bge-m3: publicadas | e5-base: top-1 | e5-base: publicadas |
|---|---|---|---|---|
| Similaridade pura | 0,59 | 0 | 0,57 | 0 |
| kNN na Folha-verdade | 0,31 | 0 | 0,26 | 0 |
| Regressão logística ("certo pela Régua") | 0,63 | 0 | 0,69 | 0 |
| MLP pequeno | 0,58 | 0 | 0,68 | 0 |
| **Logística por massa do Ramo** | 0,67 | **28 de 28** | 0,73 | 0 |
| Por Ramo, sem a Origem | 0,66 | 27 de 27 | 0,74 | 0 |

O e5-base acerta mais no top-1, mas espalha os erros pelo topo da lista. O que a Régua exige é um topo limpo, e é aí que o bge-m3 por Ramo ganha. Também descartei: sinais extras da hierarquia (aumentam o top-1, mas puxam um erro para a 17ª posição); votos dos LLMs da v1 (seriam um modelo de linguagem votando por tabela); embeddings por API (cota e custo).

## b) Os 100 rótulos

**Como usei.** Todos em validação cruzada estratificada (10 folds, por disciplina e Fora), sem holdout: com 371 Nós, separar 30 deixaria o treino pobre e o teste ainda mais incerto. Cada Questão foi pontuada por um Ranqueador que não a viu, e o kNN só via as Questões de treino do fold. Essas pontuações escolheram o Ranqueador, o limiar e a confiança, e são a base da previsão.

**O que mostraram sobre o sistema.** As 28 Questões de pontuação mais alta estão todas certas. Depois, os erros aparecem logo. Esse é o limite do que 100 rótulos provam: o limite inferior de Wilson ≥ 0,95 exigiria 73 acertos sem erro, e mesmo o alvo de 0,97 exigiria 32. Por isso o alvo é a taxa suavizada ≥ 0,96, com o intervalo largo declarado (ADR 0008). Sem a Origem, o resultado quase não muda (27 de 27), o que importa porque as Questões novas quase não têm Origem útil.

**O que mostraram sobre a convenção da equipe**

- **Fora é mais amplo do que parece.** 8 de 100 são Fora, inclusive questões sobre fixação da pena. Os dois erros mais confiantes do sistema são esses. A v1, com dois LLMs votando, publicou 4 deles e ficou em 0,90 na Folha-verdade.
- **Execução penal vai para a LEP**, quase sempre em Legislação Especial (4 vezes contra 1 em Processo Penal).
- **Os exemplos cobrem 61 dos 371 Nós.** Nos outros, quem decide é o Tema enriquecido.
- **Os 100 são antigos (Q0001–Q0359).** A Origem vira Nó em 59% das antigas e em 19% das novas.

## c) Diagnóstico

**Nos temas.** Oito temas existem em duas disciplinas, e um nono tem título com erro de digitação ("Estaturo de Idoso"), por isso nem é reconhecido como duplicado. 333 descrições são automáticas, e a contagem que trazem empurra para as Lixeiras ("Teoria da Pena", 453; "Sistemas e Princípios Processuais Penais", 538). Fatias de apostila ("Teoria da Pena (Parte 1)") viraram Nós.

**Nas questões.** A Origem engana (a Q0016 vem como Constitucional e é sobre prisão) e traz disciplinas fora da árvore (Penal Militar). 94 Questões não têm comando.

**O que o sistema ainda erra (os 33 erros do top-1 fora do fold)**

| Tipo | Exemplos | O que resolveria |
|---|---|---|
| Fora pela equipe, posto num Tema genérico | Q0043 e Q0252, em "Teoria da Pena" | O critério de Fora da equipe (pedido ao Professor) e mais exemplos de Fora |
| Lixeira atrai o específico | LEP e teorias da pena da Criminologia caem em "Teoria da Pena" | Descrição do Tema aprovada pelo Professor; mais exemplos de LEP |
| Homônimos entre disciplinas | Tráfico, LEP, Juizado, Estatuto do Idoso | Decidir o lado de cada um (memo) |
| Contexto diferente do assunto | Q0316 e Q0202: o enunciado fala do crime, o tema é Erro de Tipo | Exemplos rotulados desse padrão |
| Temas vizinhos | Provas em Espécie e Teoria Geral das Provas; Sentença e Recursos | Descrições que digam o que não entra (já enriquecidas) e mais exemplos |

Os erros de pontuação alta são quase todos dos dois primeiros tipos. Os de pontuação baixa já vão para a fila.

## d) Produção: 50 mil questões por semana

**Custo e tempo.** A decisão roda na CPU: 659 Questões levam ~1 minuto (dominado pela validação cruzada e pelo bootstrap; a decisão em si leva segundos). O embedding de cada Questão nova é local: ~2 s por Questão na CPU de 4 núcleos usada aqui, ou seja, ~28 horas por semana para 50 mil numa máquina comum, ou minutos numa GPU modesta, sem custo por chamada. O enriquecimento só roda quando a árvore muda. **O gargalo é o Professor:** com a cobertura de hoje, ~78% vão para a fila.

**Como a correção do Professor vira treino**

1. Cada Questão revisada vira um par (Questão, Nó certo) e entra no índice das vizinhas no mesmo dia.
2. **Auditoria semanal às cegas:** 50 publicadas sorteadas. São os únicos rótulos sem viés de seleção, e só eles medem a precisão; a fila só traz as difíceis.
3. A fila é ordenada pela incerteza do Ranqueador (aprendizado ativo), e os Temas sem exemplo entram primeiro.

**De quanto em quanto tempo retreinar.** Toda semana, porque o treino leva segundos, com o limiar recalibrado na janela das últimas semanas. Com ~200 rótulos auditados, o critério passa ao limite inferior do intervalo (ADR 0008). Há retreino extra quando a árvore muda, quando a auditoria tem 3 erros ou mais em 50 (a publicação automática para), quando os sinais de um lote de importação mudam mais de 5 pontos e quando um Tema recebe o dobro da taxa normal de reportes.

## O que faria com mais tempo

1. Mais exemplos de Fora e de Temas sem exemplo, pedidos ao Professor por aprendizado ativo.
2. Validação aninhada para escolher sinais e hiperparâmetros sem otimismo.
3. Ajustar o modelo de embeddings com os rótulos acumulados.

## e) Memo ao professor

Em [`memo-professor.md`](memo-professor.md).
