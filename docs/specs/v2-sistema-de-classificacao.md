# Especificação: case v2, sistema de classificação sem LLM na decisão

## Problema

A plataforma precisa pôr cada Questão no Tema certo da Árvore de temas e decidir se ela vai direto ao aluno (Publicar), à fila do Professor (Revisar) ou sai do recorte (Fora). Das publicadas, pelo menos 95% precisam estar certas (Régua), e quanto mais publicar, melhor.

A v1 resolveu isso com dois modelos de linguagem votando. Medida contra a Folha-verdade, ela acertou 75 de 83 publicadas (0,90), abaixo da Régua. Os erros vieram de uma convenção da equipe que nenhum LLM descobre sozinho: Fora mais amplo que o esperado e execução penal na LEP. A etapa complementar proíbe modelo de linguagem na decisão e pede um sistema próprio, que aprenda com os dados e devolva uma probabilidade calibrável.

## Solução

Um Ranqueador próprio, alimentado pelo conhecimento organizado a partir dos dados:
- Árvore de temas com Temas enriquecidos;
- leis citadas e o dicionário de leis;
- Origem;
- Questões vizinhas da Folha-verdade;
- embeddings locais em cache.

Para cada Questão, os sinais levantam Candidatos, o Ranqueador dá a cada um a probabilidade de estar certo pela Régua, e a regra de decisão publica acima de um limiar calibrado na Folha-verdade por validação cruzada.

Modelo de linguagem só entra antes da decisão, para enriquecer os Temas. Ele vê apenas a Árvore, tem prompt versionado e a saída fica guardada como dado. O comando de entrega regenera o `publicacao.csv` lendo só artefatos versionados, sem chamar modelo nenhum.

## Requisitos (do PDF v2)

1. `publicacao.csv` com as 659 Questões no formato do LEIA-ME.
2. `previsao.txt` com a precisão e a cobertura previstas, cada uma com intervalo, medidas nas Questões fora da Folha-verdade, e a explicação.
3. Um comando que regenera o `publicacao.csv` a partir dos anexos sem chamar modelo de linguagem, com os artefatos versionados e um README que diga como rodar, quanto tempo leva e de onde veio cada artefato, com as decisões tomadas à mão.
4. Relatório de até 4 páginas: a) o sistema; b) os 100 rótulos; c) diagnóstico; d) produção; e) memo ao Professor (1 página).
5. Acerto pela Régua: o Ramo do Tema central ou de um Extra. Subtema irmão é erro.

## Decisões de implementação (grill de 20 e 21/10/2026, Q1–Q23)

- **Repositório:** o mesmo, com a tag `v1` na entrega anterior e o trabalho na branch `develop_v2`.
- **Código por versão:** `src/classificacao/{nucleo,v1,v2}`. Uma versão nunca importa da outra. Dados, prompts, anexos, testes e entregas também ficam em pastas por versão.
- **v1 congelada e executável:** `classificacao v1 entrega` regenera `entregas/v1/` byte a byte.
- **Entrega:** a raiz recebe a entrega v2 e a v1 fica em `entregas/v1/`. As ADRs seguem numa sequência única: a v2 começa na 0008, e as ADRs 0002, 0006 e 0007 passam a substituídas.
- **Votos de LLM da v1:** fora da v2. Não entram como feature, nem como pseudo-rótulo, nem como Candidato.
- **Enriquecimento:** `claude -p sonnet` descreve os 371 Nós que podem receber Questão (o que entra, o que não entra, termos, leis). O prompt fica em `prompts/v2/enriquecedor/` com rótulo `enriquecedor/vN@hash`, e a saída em `dados/v2/temas_enriquecidos.jsonl`.
- **Revisão do enriquecimento:** checagens automáticas mais uma amostra de 30 Nós revisada pelo autor, focada nos Temas duplicados e nas Lixeiras.
- **Embeddings:** só locais na CPU, bge-m3 comparado com multilingual-e5-base pela validação cruzada. O cache fica em `dados/v2/embeddings/<modelo>/` com um manifesto de linhagem (modelo, revisão, hash dos textos, versão do enriquecimento). As dependências pesadas ficam no grupo `embeddings`, fora do caminho da entrega.
- **Sinais:**
  - similaridade da Questão com o Tema enriquecido;
  - BM25 dos termos;
  - kNN na Folha-verdade;
  - lei citada para Nó;
  - Origem para Nó;
  - estrutura da Árvore (nível, Lixeira, Tema duplicado).
- **Ranqueador:** a similaridade pura, o kNN, a regressão logística e um MLP pequeno são comparados na mesma validação cruzada. Fica o que der mais cobertura com a precisão suavizada ≥ 0,97.
- **Folha-verdade:** sem holdout. Entra toda em validação cruzada estratificada (disciplina e Fora), e as probabilidades fora do fold alimentam a calibração, o limiar e a previsão.
- **Limiar:** a precisão suavizada por Laplace fora do fold ≥ 0,97, e não o limite inferior ≥ 0,95, que com 100 rótulos exigiria 73 acertos sem nenhum erro. A análise vai para o notebook, a seção b, o `previsao.txt` e a ADR 0008.
- **Fora:** só com sinal forte. O perfil "parece Fora" vai para Revisar.
- **Tema duplicado:** publica no lado que a Folha-verdade mostra. Sem exemplo, vai para Revisar.
- **Notebooks:** `notebooks/` para a análise e a comparação, com as saídas salvas, lendo as funções de `src/`. A entrega sai só pela CLI. Docker Compose com Jupyter é opcional.
- **Mudança de distribuição:** as Q0360–Q0659 são novas, e a previsão compara as features entre as antigas e as novas antes de fechar o intervalo.

## Decisões de teste

- **Domínio em TDD:** Régua, leis, decisão, calibração e Candidatos.
- **`tests/v2/unit/`** usa fakes e nunca chama rede nem modelo.
- **`tests/v2/contrato/`** usa os anexos reais e os artefatos versionados: dicionário, temas enriquecidos e cache de embeddings.
- **A entrega se valida sozinha:** 659 linhas, sem Nó inativo, motivo onde é obrigatório e confiança em [0, 1].
- **v1 congelada:** a regeneração byte a byte continua coberta.

## Fora do escopo

- Qualquer modelo de linguagem escolhendo, votando ou validando o Tema.
- Fine-tuning de embeddings.
- Infraestrutura de produção: ela fica descrita na seção d, não construída.
- A apresentação HyperFrames da v2, que só entra se sobrar tempo.
