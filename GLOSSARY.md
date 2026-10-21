# Classificação de tópicos

Vocabulário para decidir em qual ponto da árvore de temas cada questão de concurso deve ficar, e se ela pode ir direto para o aluno.

## Árvore de temas

**Árvore de temas**:
Hierarquia de três níveis (Disciplina → Tema → Subtema) em que as questões são classificadas.
_Avoid_: Taxonomia, lista de temas

**Nó**:
Qualquer item da árvore de temas, de qualquer nível.
_Avoid_: Tópico, categoria

**Disciplina**:
Nó de nível 0, raiz de um ramo (Penal, Processo Penal, Direito Penal - Legislação Especial, Criminologia).
_Avoid_: Matéria, área

**Tema**:
Nó de nível 1, filho direto de uma Disciplina.
_Avoid_: Assunto, tópico

**Subtema**:
Nó de nível 2, filho direto de um Tema.
_Avoid_: Subassunto, subtópico

**Ramo**:
Um Nó junto com seu pai e seus filhos diretos; publicar em qualquer Nó do mesmo Ramo do gabarito conta como acerto.
_Avoid_: Família, linha

**Nó inativo**:
Nó com status inativo, que nunca pode receber questões.

**Tema duplicado**:
Tema cujo título se repete num Tema de outra Disciplina; seus Subtemas herdam a condição.

**Lixeira**:
Nó genérico ou introdutório que atraiu questões que não têm relação com ele.
_Avoid_: Tema genérico, catch-all

**Tópico**:
Palavra usada apenas na fala do aluno ("estudo por tópico"); não designa nenhum nível da árvore.

## Classificação

**Questão**:
Item de concurso com enunciado, comando e alternativas, identificado por um id do case (Q0001…).

**Origem**:
Disciplina e assunto atribuídos pelo site de onde a Questão veio; podem estar errados e não pertencem à Árvore de temas.
_Avoid_: Rótulo, classificação original

**Tema central**:
O Nó escolhido como lugar principal de uma Questão; pode ser um Tema ou um Subtema, apesar do nome.
_Avoid_: Rótulo, categoria principal

**Extras**:
Outros Nós que a Questão também cobre, além do Tema central.

**Gabarito**:
O Tema central e os Extras atribuídos pela equipe de especialistas às Questões avaliadas, usados para avaliar a entrega e nunca vistos por nós.
_Avoid_: Ground truth, rótulo verdadeiro

**Folha-verdade**:
As 100 Questões cujo Gabarito a equipe nos entregou (v2), com Tema central, Extras e a marca de Fora; servem para treinar, calibrar e prever, e não entram na avaliação.
_Avoid_: Amostra, gabarito conhecido, dataset de treino

**Confiança**:
Probabilidade calibrada de o Tema central estar certo pela Régua. Na v2, vem do Ranqueador calibrado na Folha-verdade; na v1, era a taxa de acerto suavizada (Laplace) do mesmo grupo na Amostra de calibração. Não confundir com a confiança que um modelo de linguagem declara no voto (v1).

## Papéis

**Ranqueador**:
O sistema que decide na v2: ordena os Candidatos de cada Questão e dá a cada um a probabilidade de estar certo pela Régua, sem chamar nenhum modelo de linguagem.
_Avoid_: Classificador (é o papel de LLM da v1), modelo, IA

**Candidatos**:
Os poucos Nós que concorrem ao Tema central de uma Questão, levantados pelos sinais (similaridade, Questões vizinhas da Folha-verdade, lei citada, Origem) antes de o Ranqueador ordenar.

**Tema enriquecido**:
Nó com descrição do que entra e do que não entra, termos-chave e leis típicas, gerados por modelo de linguagem a partir só da Árvore de temas e guardados como dado revisado.

Os papéis abaixo são de modelos de linguagem e existem só na v1; na v2, nenhum modelo de linguagem escolhe, vota ou valida o Tema.

**Classificador**:
(v1) Primeiro modelo, que propõe o Tema central e os Extras de uma Questão vendo também a Origem.

**Verificador**:
(v1) Segundo modelo, que classifica a mesma Questão de forma independente, sem ver a Origem nem a proposta do Classificador.
_Avoid_: Revisor

**Desempatador**:
(v1) Terceiro modelo, acionado só quando Classificador e Verificador discordam; escolhe a sugestão que vai para o Professor e nunca publica.
_Avoid_: Juiz (num produto jurídico, sugere uma autoridade que decide; até 18/10/2026 era esse o nome do papel)

**Classificador treinado**:
(v1, ADR 0007) Em produção, modelo treinado sobre embeddings que seria um dos dois votos ao lado de um modelo de linguagem. Na v2, deu lugar ao Ranqueador.

**Prompt do papel**:
Instruções de sistema que um papel (Classificador, Verificador ou Desempatador) recebe antes da Árvore de temas, guardadas em `prompts/<papel>/`.
_Avoid_: Prompt do sistema, instrução

**Versão do prompt**:
Um texto fixo do Prompt do papel (`v1`, `v2`…), identificado em cada voto por `papel/versao@hash`; mudar o texto cria uma versão nova.

**Rotulador**:
(v1) Modelo fora do pipeline que responde a Amostra de calibração às cegas, sem ver Origem nem votos; é segunda opinião, não fonte de rótulo (ADR 0006).

**Professor**:
O especialista humano em Direito que atende a fila de Revisar.
_Avoid_: Revisor, especialista

**Concordância**:
(v1) Classificador e Verificador apontam Nós do mesmo Ramo para a mesma Questão.

## Decisão

**Decisão**:
O destino de cada Questão: Publicar, Revisar ou Fora.

**Publicar**:
A Questão vai direto para o aluno no Tema central; errar aqui é o erro mais caro.

**Revisar**:
A Questão vai para a fila do professor, levando o Tema central como sugestão.

**Fora**:
Nenhum Nó ativo da Árvore de temas serve para a Questão.

**Indício de injeção**:
Trecho do texto de uma Questão que fala com o modelo em vez de com o aluno (ordem de ignorar instruções ou de classificar num Nó, campo do voto, marcador de papel); a Questão vai para Revisar sem passar por nenhum modelo.
_Avoid_: Ataque, questão maliciosa

**Amostra de calibração**:
(v1; substituída pela Folha-verdade) As Questões sorteadas cuja resposta certa é levantada (neste case, por um agente jurídico especializado; ADR 0006) para calibrar o limiar e prever a Precisão; substitui o Gabarito, que nunca vemos.

**Régua**:
Exigência de que pelo menos 95% das Questões publicadas estejam no mesmo Ramo do Tema central ou de um dos Extras do Gabarito; publicar num Subtema irmão é erro.

**Precisão**:
Fração das Questões publicadas que estão certas pela Régua.

**Cobertura**:
Fração do total de Questões que recebeu a Decisão Publicar.
