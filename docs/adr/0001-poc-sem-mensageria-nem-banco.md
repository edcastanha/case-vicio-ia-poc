# POC sem mensageria nem banco: fila e DLQ em arquivo

Para as 359 Questões do case, o pipeline roda em Python puro: cada Questão tem um estado persistido em disco, as chamadas têm retry com backoff, e as que falham após N tentativas vão para uma DLQ em arquivo e terminam como Revisar ("falha do provedor X"). Ao final, a geração da entrega falha se `publicacao.csv` não tiver exatamente uma linha por Questão. A Árvore de temas (377 Nós) cabe inteira num prompt e a relação pai/filho é um dicionário em memória, então banco de grafo não acrescenta nada; embeddings ficam num array em memória.

RabbitMQ (ou Redis) com DLQ, e um banco vetorial para busca de Nós candidatos, foram considerados e **adiados de propósito**: o enunciado diz que infraestrutura sofisticada não pesa, o prazo é de 3 dias, e o que pesa (cobertura sob a Régua e acerto da previsão) depende de prompts e calibração, não de infra. Esse desenho é o correto para produção (50 mil Questões/semana) e é descrito na seção de produção do relatório.

## Consequences

- As portas `FilaDeFalhas` e `Cache` existem na camada de aplicação; trocar a implementação em arquivo por RabbitMQ/Redis é um novo adaptador, sem mudar o domínio.
