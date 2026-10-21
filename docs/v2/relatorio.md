# Relatório v2: um sistema de classificação sem modelo de linguagem na decisão

> **Em resumo.** ⟨publicadas⟩ das 559 Questões avaliadas (⟨cobertura⟩) vão direto ao aluno. Prevejo que ⟨precisão⟩ delas estejam certas (⟨intervalo⟩). Quem decide é um Ranqueador treinado nos 100 exemplos da equipe. Nenhum modelo de linguagem escolhe, vota ou valida o Tema, e `uv run classificacao v2 entrega` regenera tudo em segundos, sem rede.

## a) O sistema, peça por peça

O problema não é achar o Tema de cada Questão: é saber **quando o sistema pode confiar em si mesmo**. Por isso cada peça existe para gerar um sinal que separa acerto de erro, e a decisão é de um modelo pequeno, calibrado nos exemplos da equipe.

| Peça | O que faz | Por que está ali |
|---|---|---|
| Limpeza do texto | Só o texto que o aluno lê (sem CSS do Word nem caracteres invisíveis) | Herdada da v1; o lixo do HTML distorce qualquer sinal |
| Temas enriquecidos | Um modelo de linguagem descreveu os 371 Nós (o que entra, o que não entra, termos, leis), **vendo só a Árvore**, com prompt versionado | 333 dos 377 temas tinham descrição automática ("44 questões no source"), sem nada que separe um Tema do vizinho |
| Embeddings locais | Vetores das Questões e dos Temas enriquecidos, gerados na CPU por modelos abertos e guardados no repositório | Similaridade de assunto, sem custo nem cota, reproduzível por qualquer um |
| Leis citadas | Regex para "Lei nº 11.340/2006", "Lei Maria da Penha", "LEP"… e um dicionário de 29 leis para os seus Nós | Uma lei citada diz o assunto. Aparece em 113 Questões e aponta o Ramo certo em 9 de 13 exemplos |
| Origem para Nó | O assunto de origem, sem "(Parte 01)", casado com o título de um Nó | Sinal barato, mas fraco: certo em 22 de 92 exemplos |
| Vizinhas da Folha-verdade | As 5 Questões rotuladas mais parecidas votam no Nó pela Régua | É o que ensina a **convenção da equipe**, como LEP em Legislação Especial |
| Candidatos | Top-10 por similaridade, mais os Nós das leis, da Origem e das vizinhas, mais o pai de cada Subtema | Poucos Nós por Questão, e o pai sempre disponível para a dúvida entre irmãos |
| Ranqueador | ⟨tipo vencedor⟩ sobre 11 sinais por Candidato | Aprende quanto confiar em cada sinal |
| Decisão | Publica acima do limiar calibrado; Tema duplicado só com exemplo da equipe; Direito Penal Militar é Fora | Regras curtas, testadas, sem modelo |

**O que testei e descartei**

| Tentativa | Resultado | O que ficou |
|---|---|---|
| ⟨tabela da comparação: similaridade pura, kNN, logística, MLP × bge-m3, e5-base⟩ | | |
| Exigir limite inferior de Wilson ≥ 0,95 | Exigiria 73 acertos sem nenhum erro; zera a cobertura com 100 rótulos | Taxa suavizada ≥ 0,97 (ADR 0008) |
| Usar os votos dos LLMs da v1 como sinal | Seria um modelo de linguagem votando por tabela | Fora da v2 |
| Embeddings por API (Gemini) | Cota e custo; a v1 parou na 29ª Questão por cota | Modelos locais |

## b) Os 100 rótulos

**Como usei.** Todos em validação cruzada estratificada (10 folds, por disciplina e Fora). Cada Questão foi pontuada por um Ranqueador que não a viu, e o kNN só enxergava as Questões de treino do fold. Essas pontuações fora do fold escolheram o Ranqueador, o limiar e a curva de confiança, e são a base da previsão. Não separei um holdout: com 100 rótulos para 371 Nós, tirar 30 deixaria o treino pobre e o teste com intervalo ainda mais largo.

**O que mostraram sobre o sistema.** ⟨acerto do top-1, publicadas e acertos fora do fold, cobertura; ablação sem Origem⟩

**O que mostraram sobre a convenção da equipe**

- **Fora é mais amplo do que parece.** 8 de 100 são Fora, inclusive Questões que caberiam em "Teoria da Pena" ("Sobre a fixação da pena…"). A v1, com dois LLMs votando, publicou 4 delas, e medida contra a Folha-verdade acertou 75 de 83 publicadas (0,90), abaixo da Régua.
- **Execução penal vai para a LEP, quase sempre em Legislação Especial.** A equipe usou a LEP 4 vezes em Legislação Especial e uma em Processo Penal. A convenção existe, mas não é absoluta.
- **Os exemplos cobrem pouco da árvore.** São 61 Nós distintos de 371. Nos outros, a decisão depende do Tema enriquecido e das leis.
- **Os 100 são todos antigos (Q0001–Q0359).** Nas 300 novas, a Origem vira Nó em 19% das Questões, contra 59% nas antigas. É a maior fonte de incerteza da previsão.

## c) Diagnóstico

**Nos temas.** Oito temas existem em duas disciplinas. 333 descrições são automáticas, e a contagem que trazem empurra para as Lixeiras: "Sistemas e Princípios Processuais Penais" (538), "Teoria da Pena" (453), "Introdução ao Estudo do Direito Penal" (424). Há ainda fatias como "Teoria da Pena (Parte 1)" sem descrição, e erros de cadastro ("Escolas Crimonológicas").

**Nas questões.** A Origem engana (Q0016 vem como Constitucional e é sobre prisão), traz disciplinas fora da árvore (Penal Militar) e fatia assuntos como apostila. 94 Questões não têm comando.

**O que o sistema ainda erra, e o que resolveria**

| Tipo de Questão | Por que erra | O que resolveria |
|---|---|---|
| ⟨tipos, a partir dos erros fora do fold⟩ | | |
| Multitemática (cada assertiva de um assunto) | Não existe "o" tema central | Regra da equipe (pedido ao Professor) |
| Contexto diferente do assunto (Q0120) | O enunciado fala de um crime, e quem decide é a regra processual | Mais exemplos rotulados desse padrão |
| Tema sem nenhum exemplo | O kNN não tem voto, sobra a similaridade | Rótulos do Professor nesses Temas (aprendizado ativo) |

## d) Produção: 50 mil questões por semana

**Custo e tempo.** A decisão roda na CPU: sinais, Ranqueador e regra levam ⟨tempo⟩ para 659 Questões, ou seja, minutos para 50 mil. O único custo por Questão nova é o embedding, zero com o modelo local, numa máquina comum. O enriquecimento dos Temas só roda de novo quando a árvore muda. **O gargalo é o tempo do Professor**, não a máquina.

**Como a correção do Professor vira treino**

1. Cada Questão revisada vira um par (Questão, Nó certo). Ela entra no índice do kNN no mesmo dia: o kNN não precisa de treino.
2. **Auditoria semanal às cegas:** 50 publicadas sorteadas. São os únicos rótulos sem viés de seleção, e só eles medem a precisão. A fila só traz as Questões difíceis.
3. A fila é ordenada por incerteza (aprendizado ativo): o Professor rotula primeiro o que mais ensina.

**De quanto em quanto tempo retreinar.** Toda semana, com as revisões e a auditoria, porque o treino leva segundos. O limiar é recalibrado na janela das últimas 4 semanas. Há retreino extra quando a árvore muda (o enriquecimento roda de novo para os Nós afetados), quando a auditoria tem 3 erros ou mais em 50 (a publicação automática para), quando a distribuição dos sinais de um lote de importação muda mais de 5 pontos, e quando um Tema recebe o dobro da taxa normal de reportes.

## O que faria com mais tempo

1. Mais rótulos nos Temas sem exemplo, por aprendizado ativo.
2. Validação aninhada para escolher os sinais sem nenhum otimismo.
3. Ajustar o modelo de embeddings (fine-tuning) com os rótulos acumulados.

## e) Memo ao professor

Em [`memo-professor.md`](memo-professor.md).
