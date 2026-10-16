# Publicar só com Concordância entre provedores diferentes

Uma Questão só recebe a Decisão Publicar quando o Classificador (Anthropic) e o Verificador (Gemini), modelos de famílias diferentes e com entradas diferentes (só o Classificador vê a Origem), apontam Nós do mesmo Ramo **e** a Confiança calibrada passa do limiar. O limiar é calibrado na amostra rotulada às cegas pelo usuário mirando 97% de Precisão pontual, não 95%, porque com cerca de 50 rótulos o intervalo é largo e mirar a Régua exata dá cerca de 50% de chance de estourá-la.

Regras que decorrem disso e que parecem estranhas sem contexto:

- **O Juiz nunca publica.** Ele só entra no desacordo e escolhe a sugestão que vai para o Professor. Desacordo marca as Questões difíceis, e publicá-las arrisca a Régua.
- **Na dúvida entre Subtemas irmãos, publica-se no Tema pai.** Pela Régua, o Tema pai acerta qualquer um dos filhos, enquanto um Subtema errado é erro.
- **Nunca se publica numa Disciplina.** Isso recriaria a Lixeira que o case critica, e não é claro que conte como mesmo Ramo.
- **Fora exige que os dois modelos concordem** que nenhum Nó serve; qualquer dúvida vai para Revisar.
- **O modo de teste não gera a entrega.** No backend `claude-code` os três papéis viram Claude e a independência se perde, então ele serve só para testes. A exceção é quando falta a chave de algum provedor na data final: aí o fallback é declarado no relatório e a calibração é refeita nessa configuração.

## Considered Options

- Juiz desempata e publica: descartado, porque aumenta a cobertura justamente nas Questões de maior risco.
- Um único modelo com limiar de autoconfiança: descartado, porque a autoconfiança declarada por um LLM é mal calibrada e não oferece um segundo sinal independente.
