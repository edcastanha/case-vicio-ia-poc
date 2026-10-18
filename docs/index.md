# Classificação de tópicos

O aluno estuda por tema: se uma questão fica no tema errado, ele estuda a matéria errada. Este trabalho classifica 359 questões de Direito Penal, Processo Penal, Legislação Penal Especial e Criminologia na árvore de temas da plataforma e decide, para cada uma, se ela vai **direto para o aluno**, se vai para a **revisão do professor** ou se **nenhum tema serve**. A regra é que pelo menos 95% das questões publicadas estejam certas, e a parte difícil é saber, sem gabarito, quando a máquina acertou.

[Ver a apresentação interativa (9 slides)](apresentacao/index.html){ .md-button }

## Como cada questão é decidida

--8<-- "README.md:fluxo"

Dois modelos de famílias diferentes, com informações diferentes, classificam cada questão sem ver a resposta um do outro. Uma questão só é publicada quando os dois concordam e nada indica risco. O desacordo marca a questão difícil, e ela vai para o professor com uma sugestão.

## O que prevemos

Antes de conhecer o resultado, a previsão de quanto vamos acertar:

<!-- previsao -->

O texto acima é o mesmo do `previsao.txt` da entrega. A previsão vem da Amostra rotulada, e não da confiança que os modelos dizem ter. O [relatório](relatorio.md) conta como chegamos nessa regra.

## Onde ler mais

- [Relatório](relatorio.md): como pensei, o que atrapalha classificar certo e como isto rodaria em produção.
- [Relatório em PDF](https://github.com/edcastanha/case-vicio-ia-poc/blob/main/relatorio.pdf): o mesmo texto e o memo, em 5 páginas.
- [Resultados](resultados.md): cada uma das 359 questões, com o voto e a justificativa de cada modelo.
- [Memo ao Professor](memo-professor.md): o que encontramos nos temas e do que precisamos dele.
- [Decisões](adr/0002-publicar-so-com-concordancia-entre-provedores.md): o porquê de cada regra.
