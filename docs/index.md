# Classificação de tópicos

O aluno estuda por tema: se uma questão fica no tema errado, ele estuda a matéria errada. Este trabalho classifica 659 questões de Direito Penal, Processo Penal, Legislação Penal Especial e Criminologia na árvore de temas da plataforma e decide, para cada uma, se ela vai **direto para o aluno**, se vai para a **revisão do professor** ou se **nenhum tema serve**. Pelo menos 95% das publicadas precisam estar certas.

Nesta segunda etapa, **nenhum modelo de linguagem escolhe, vota ou valida o tema**. A decisão é de um sistema próprio, treinado nas 100 questões que a equipe classificou, e o comando que gera a entrega roda sem rede e sem modelo.

## Como cada questão é decidida

--8<-- "README.md:fluxo"

Para cada questão, o sistema reúne alguns temas candidatos: os mais parecidos com ela, os das leis que ela cita, o da classificação de origem e os das questões parecidas que a equipe já classificou. O Ranqueador dá a cada candidato a chance de estar certo e só publica quando essa chance, medida nos exemplos da equipe, é alta.

## O que prevemos

Antes de conhecer o resultado, a previsão de quanto vamos acertar nas 559 questões avaliadas:

<!-- previsao -->

O texto acima é o mesmo do `previsao.txt` da entrega. O [relatório](v2/relatorio.md) explica de onde vêm os números e por que o intervalo é largo com 100 exemplos ([ADR 0008](adr/0008-limiar-pela-taxa-suavizada-com-margem.md)).

## Onde ler mais

- [Relatório](v2/relatorio.md): o sistema peça por peça, os 100 rótulos, o diagnóstico e a produção.
- [Relatório em PDF](https://github.com/edcastanha/case-vicio-ia-poc/blob/main/relatorio.pdf): o mesmo texto, com o memo na última página.
- [Memo ao Professor](v2/memo-professor.md): o que encontramos nos temas e do que precisamos dele.
- [Resultados](resultados.md): a decisão, a confiança e o motivo de cada questão.
- [Análise dos dados](https://github.com/edcastanha/case-vicio-ia-poc/blob/main/notebooks/01_analise_dos_dados.ipynb): o notebook que decidiu o desenho.
- [Primeira etapa (v1)](v1/relatorio.md): dois modelos de linguagem votando, e por que isso não bastou.
