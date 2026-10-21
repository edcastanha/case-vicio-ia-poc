# Memo ao professor

**Assunto:** as 659 questões de Penal, Processo Penal, Legislação Especial e Criminologia. O que encontrei, o que recomendo mudar nos temas e cinco pedidos concretos.

## O que fiz e o resultado

Montei um sistema que aprende com as **100 questões que a sua equipe classificou**. Ele compara cada questão nova com essas 100, com uma descrição de cada tema e com as leis que ela cita, e só publica quando a chance de acerto, medida nos exemplos da equipe, é alta. **125 das 559 questões avaliadas (22%) vão direto ao aluno**, e as demais vão à sua fila com uma sugestão. Espero que **97 em cada 100 publicadas** estejam certas, e o número real deve ficar entre 78 e 100: com 100 exemplos, não dá para prometer mais do que isso. Nenhum sistema de inteligência artificial escolhe o tema: ele só ajudou a escrever, antes, as descrições dos temas, que passam por revisão humana.

## O que recomendo mudar nos temas

- **Oito temas existem em duas disciplinas**, como a Lei de Execução Penal em Processo Penal e em Legislação Especial. A equipe usou os dois lados.
- **As descrições não descrevem.** 333 temas dizem só "Subtema de X. N questões". Um parágrafo sobre o que entra e o que não entra em cada tema ajuda a máquina e o aluno. As descrições que geramos estão prontas para o senhor aprovar.
- **Temas genéricos acumulam questões de outros**: "Teoria da Pena", "Introdução ao Estudo do Direito Penal" e "Sistemas e Princípios Processuais Penais".
- **Fatias de apostila viraram temas**, como "Teoria da Pena (Parte 1)" e "(Parte 2)". Elas confundem o aluno e a máquina.

## Do que preciso do senhor

**1. Decidir o lado de cada tema duplicado** (uma vez só, oito decisões). Hoje a regra é publicar no lado que a equipe usou nos exemplos e mandar o resto para a fila.

| Tema | Sugestão: fica em | Sai de |
|---|---|---|
| Lei de Execução Penal | Legislação Especial | Processo Penal |
| Ação Penal | Processo Penal | Penal |
| Tráfico de Drogas, Lei Maria da Penha, Crimes Ambientais, Abuso de Autoridade, Lavagem de Dinheiro e Organizações Criminosas | Legislação Especial | Penal |

**2. Aprovar as descrições de 30 temas** (uma planilha, cerca de 20 minutos). Basta marcar "ok" ou corrigir. Começa pelos duplicados e pelos genéricos.

**3. Dizer o que é "fora" para a equipe.** Nos exemplos, 8 de 100 são fora, inclusive questões sobre fixação da pena e aplicação da lei penal, que a árvore parece cobrir. Uma frase sobre o critério evita que o sistema publique essas questões.

**4. Revisar a fila na ordem que ela chega.** As primeiras são as que mais ensinam ao sistema, e cada revisão vira exemplo no mesmo dia.

**5. Toda semana, conferir 50 questões publicadas, sorteadas e sem ver a resposta do sistema.** Se 3 ou mais estiverem erradas, a publicação automática para até corrigirmos.
