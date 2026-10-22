# Limiar pela taxa suavizada com margem, não pelo limite inferior do intervalo

Na v2, o Ranqueador publica uma Questão quando a pontuação dela passa de um limiar escolhido na Folha-verdade por validação cruzada. O limiar é o de **maior cobertura em que a taxa de acerto suavizada por Laplace, (acertos + 1) / (publicadas + 2), das Questões acima dele fica ≥ 0,96**. O 0,96, e não 0,95, é a margem sobre a Régua.

## Por que não exigir que o limite inferior do intervalo passe de 95%

Seria o critério mais seguro: publicar só onde houvesse 95% de confiança estatística de cumprir a Régua. Com 100 rótulos, ele não publica quase nada. O limite inferior de Wilson só passa de 0,95 com:

| Erros acima do limiar | Acertos necessários |
|---|---|
| 0 | 73 |
| 1 | 109 |
| 2 | 140 |
| 3 | 170 |

A Folha-verdade tem 92 Questões dentro da Árvore de temas. Com um único erro, nem os 100 rótulos bastariam, e mesmo sem erro seria preciso publicar quase todas as Questões dentro da árvore e acertar todas. Na prática, esse critério zera a cobertura, e a cobertura é metade do que a Régua pede.

## Consequências

- **A previsão diz a verdade sobre a incerteza.** O ponto previsto é a taxa suavizada, e o intervalo (Wilson e bootstrap) é largo e declarado no `previsao.txt`. Não fingimos uma garantia que 100 rótulos não dão.
- **A margem é o seguro.** Mirando 0,96, um desvio de 1 ponto entre a Folha-verdade e as 559 Questões avaliadas ainda deixa a precisão na Régua.
- **Mais rótulos estreitam o intervalo.** Em produção, a auditoria semanal do Professor (50 publicadas sorteadas) soma rótulos sem viés de seleção. Em poucas semanas há rótulos para trocar este critério pelo limite inferior.

## Por que 0,96, e não 0,97 como na v1

O alvo começou em 0,97, a margem da v1. Com os 100 rótulos, ele exige 32 acertos seguidos no topo da lista fora do fold, sem nenhum erro: (32 + 1) / (32 + 2) = 0,971. O melhor Ranqueador (massa por Ramo) chega a 26 a 30 acertos seguidos, conforme a semente da validação cruzada, antes do primeiro erro. Com 0,97, a cobertura seria zero, e a decisão de publicar nada não depende da qualidade do sistema, só do tamanho da amostra. Com 0,96, publica-se o topo da lista até perto do primeiro erro, e a margem de 1 ponto continua sobre a Régua. A decisão foi tomada com o autor em 21/10/2026.

## Considered Options

- **Manter 0,97 e esperar o modelo melhorar:** descartado. Com 100 rótulos, a diferença entre 28 e 32 acertos seguidos é ruído de amostra, e a entrega sairia com cobertura zero.

- **Limite inferior de Wilson ≥ 0,95:** descartado pela tabela acima.
- **Taxa bruta ≥ 0,95 (sem suavização nem margem):** descartado. Com 30 acertos seguidos daria 100% e publicaria no ponto em que um único erro a mais derruba a Régua.
- **Bootstrap do procedimento como único critério (v1):** sem nenhum erro na amostra, ele diz 1,00 sem margem (ADR 0002). Ele continua no intervalo da previsão, mas não escolhe o limiar.
