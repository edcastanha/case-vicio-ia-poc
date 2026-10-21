# Amostra de calibração rotulada por um agente jurídico especializado, sem arbitragem

Substitui o ADR 0004. As 50 Questões da Amostra de calibração (`dados/v1/rotulagem.csv`) foram rotuladas uma a uma por um agente de IA especializado (GPT 5.6 Terra, da OpenAI), com uma skill feita para questões jurídicas, conduzido pelo autor do case. A coluna `resposta` tem o Nó escolhido, e a `observacao` tem a justificativa de cada escolha. Não houve um especialista humano em Direito: o case não tinha acesso a um advogado ou professor da área para a rotulagem.

A arbitragem do ADR 0004 foi descartada, com o `classificacao v1 consolidar`, a planilha A/B e o Conflito. Ela existia para um humano decidir só onde o Rotulador e o pipeline divergiam, e esse humano não existe neste case. O Rotulador continua como segunda opinião às cegas: `classificacao v1 rotular` grava `dados/v1/rotulador.json` e mede quantas respostas dele caem no Ramo do rótulo da Amostra. Ele não gera rótulo.

## O que os rótulos mostraram

| | No Ramo do rótulo |
|---|---|
| Concordância entre Classificador e Verificador (o que pode ser publicado) | 40 de 40 (35 no mesmo Nó, 5 no mesmo Ramo) |
| Desacordo (nunca publicado; o Nó é a sugestão do Desempatador) | 7 de 10 |
| Rotulador (Opus, às cegas) | 46 de 50 |

## Limitações declaradas

Estas limitações entram no relatório junto da previsão de Precisão:

- **O gabarito da calibração é de um modelo, não de um especialista.** A previsão mede o quanto o pipeline concorda com um agente jurídico, e não com o Professor. Se o agente erra junto com os modelos do pipeline, o erro chega à amostra como acerto, e a Precisão prevista fica otimista. O agente é de outra família (GPT, da OpenAI) que o Classificador (Claude) e o Verificador e o Desempatador (DeepSeek). Isso reduz os erros em comum, mas não os elimina, porque os três foram treinados em textos jurídicos parecidos.
- **Os 50 rótulos saíram de dentro da lista de candidatos da planilha.** A lista é cega quanto à fonte, mas sempre contém os Nós votados pelo pipeline, embaralhados com homônimos (Temas duplicados) e Nós de preenchimento. Um rotulador que escolhe dentro da lista nunca aponta um Nó em que nenhum modelo pensou, e isso também puxa a Precisão prevista para cima.
- **Temas duplicados são convenção, não Direito.** Na Q0036 (Lei Maria da Penha) e na Q0087 (Lei de Execução Penal), o assunto é inequívoco, e a escolha entre as Disciplinas repetidas é uma convenção do catálogo. Por isso essas Questões nunca são publicadas (ADR 0002).

A mitigação em produção é o Professor revisar uma parte sorteada das publicadas. É a auditoria amostral da seção c) do relatório, e ela substitui esta amostra por uma humana com o tempo.

## Considered Options

- **Rotulagem assistida com arbitragem humana (ADR 0004):** descartada, porque não há o humano especialista que ela pressupõe. Fazer a arbitragem com o mesmo agente só repetiria a rotulagem com menos contexto.
- **Usar o Rotulador como gabarito:** descartado. Ele é Opus, da mesma família do Classificador, e não tem a skill jurídica nem justifica cada escolha para auditoria.
- **Esperar um especialista humano:** é o padrão-ouro, mas não está disponível. A amostra, as justificativas e o código ficam prontos para ser refeitos por ele, porque `entrega` só lê a coluna `resposta`.
