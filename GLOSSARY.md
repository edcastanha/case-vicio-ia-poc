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
O Tema central atribuído pela equipe de especialistas, usado para avaliar a entrega e nunca visto por nós.
_Avoid_: Ground truth, rótulo verdadeiro

**Confiança**:
Probabilidade estimada de o Tema central estar no mesmo Ramo do Gabarito.

## Papéis

**Classificador**:
Primeiro modelo, que propõe o Tema central e os Extras de uma Questão vendo também a Origem.

**Verificador**:
Segundo modelo, que classifica a mesma Questão de forma independente, sem ver a Origem nem a proposta do Classificador.
_Avoid_: Revisor

**Juiz**:
Terceiro modelo, acionado só quando Classificador e Verificador discordam; escolhe a sugestão que vai para o Professor.

**Professor**:
O especialista humano em Direito que atende a fila de Revisar.
_Avoid_: Revisor, especialista

**Concordância**:
Classificador e Verificador apontam Nós do mesmo Ramo para a mesma Questão.

## Decisão

**Decisão**:
O destino de cada Questão: Publicar, Revisar ou Fora.

**Publicar**:
A Questão vai direto para o aluno no Tema central; errar aqui é o erro mais caro.

**Revisar**:
A Questão vai para a fila do professor, levando o Tema central como sugestão.

**Fora**:
Nenhum Nó ativo da Árvore de temas serve para a Questão.

**Régua**:
Exigência de que pelo menos 95% das Questões publicadas estejam no mesmo Ramo do Gabarito.

**Precisão**:
Fração das Questões publicadas que estão no mesmo Ramo do Gabarito.

**Cobertura**:
Fração do total de Questões que recebeu a Decisão Publicar.
