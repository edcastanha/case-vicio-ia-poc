# Classificação de tópicos — case Vício

Classifica 359 questões de Penal, Processo Penal, Legislação Penal Especial e Criminologia na árvore de temas da plataforma e decide, para cada uma, **publicar**, **revisar** ou **fora**, sob a régua de ≥ 95% de precisão nas publicadas. Enunciado: [`case-ia-classificacao-de-topicos.pdf`](case-ia-classificacao-de-topicos.pdf). Dados: [`anexos-case-ia.zip`](anexos-case-ia.zip) (lido direto, sem extrair).

> **Configuração usada na entrega:** Classificador = `claude -p` com `sonnet` (assinatura Claude Code, sem chave da API da Anthropic), Verificador = `deepseek-flash`, Juiz = `deepseek-v4-pro`, embeddings = `gemini-embedding-2`. Classificador e Verificador são de famílias diferentes, que é o que a regra de publicação exige (ADR 0002). O Verificador planejado era o `gemini-3.8-flash`, mas a chave do Gemini disponível é do plano gratuito, que permite 20 chamadas por dia. A tentativa parou na 29ª Questão, e a rodada completa com DeepSeek foi mantida. A calibração foi feita nessa mesma configuração.

## Como funciona, em uma frase por etapa

1. **Classificador** (Anthropic, Sonnet via `claude -p`) escolhe o nó da árvore vendo a questão e a classificação de origem.
2. **Verificador** (DeepSeek, `deepseek-flash`) escolhe de forma independente, **sem** ver a origem nem o Classificador.
3. **Juiz** (DeepSeek, `deepseek-v4-pro`) só entra quando os dois discordam, e só escolhe a sugestão que vai para o professor: **nunca publica**.
4. **Embeddings** (Gemini, `gemini-embedding-2`) dão um sinal extra (similaridade) e uma sugestão de reserva.
5. **Publica** só quem tem concordância de ramo entre dois provedores diferentes, nenhum modelo em dúvida, tema não duplicado e pontuação acima do limiar calibrado em uma amostra rotulada às cegas por um humano, mirando 97%.

As regras e o porquê de cada uma estão em [`docs/adr/`](docs/adr/); o vocabulário, em [`GLOSSARY.md`](GLOSSARY.md).

Para ler o raciocínio e os resultados sem abrir o código, há um site em [edcastanha.github.io/case-vicio-ia-poc](https://edcastanha.github.io/case-vicio-ia-poc/), gerado destes mesmos arquivos com MkDocs. Para ver localmente: `uv run mkdocs serve`.

## Como rodar

Requer [uv](https://docs.astral.sh/uv/) e as três chaves de API.

```bash
uv sync
cp .env.example .env              # preencha as chaves
uv run pytest                     # testes (nenhum chama rede)

uv run classificacao rodada       # 1. classifica as 359 (retomável; cache em dados/cache)
uv run classificacao sinais       # 2. embeddings: similaridade e reserva
uv run classificacao amostra      # 3. gera dados/rotulagem.csv (50 questões, cega)
#                                   4. preencha `resposta` (id do nó, "id — caminho" de um candidato
#                                      ou "nenhum"); neste case, por um agente jurídico (ADR 0006)
uv run classificacao rotular      # 5. opcional: o Rotulador (Opus) responde às cegas, como segunda opinião
uv run classificacao entrega      # 6. calibra nos rótulos e grava publicacao.csv e previsao.txt
```

O que gera o `publicacao.csv`: o passo 6, a partir de `dados/rodada/classificacoes.jsonl` (passo 1), `dados/rodada/sinais.json` (passo 2) e `dados/rotulagem.csv` (passos 3 e 4). Falhas de provedor vão para `dados/rodada/falhas.jsonl` e a questão termina em `revisar`; a entrega se recusa a gravar um arquivo fora do formato do LEIA-ME.

## Prompts

O prompt de cada papel fica em [`prompts/<papel>/<versao>.md`](prompts/), e a versão ativa, em [`prompts/versoes.toml`](prompts/versoes.toml). Para testar uma versão nova, crie `prompts/classificador/v2.md` e rode o piloto com `CLASSIFICADOR_PROMPT=v2`. Uma versão publicada nunca é editada (ADR 0003). Cada voto grava o prompt que o gerou (`classificador/v1@dce3cb01`), e `entrega` recusa rodadas com versões misturadas: mudou o prompt, refaça a rodada e a calibração.

`uv run classificacao piloto --n 30` roda uma amostra; com `*_BACKEND=claude-code` no `.env` usa o `claude -p` local em vez das APIs (só para teste).

## Código

Clean Architecture em `src/classificacao/`, com dependências apontando para dentro:

| Camada | O que tem |
|---|---|
| `dominio/` | árvore e regra do ramo, decisão (publicar/revisar/fora), pontuação, calibração (limiar, bootstrap, curva), validação da entrega |
| `aplicacao/` | casos de uso (classificar questão, processar lote, sinais, amostra cega, calibração, entrega), portas e prompts |
| `adaptadores/` | Anthropic, Gemini, DeepSeek, `claude -p`, leitura do zip, planilha de rotulagem, cache/DLQ/registro em arquivo |
| `entrada/` | linha de comando, configuração por `.env` e páginas geradas do site (`site.py`, chamado por `docs/hooks/site.py`) |

Testes em `tests/unit/` (regras, com fakes) e `tests/contrato/` (adaptadores, com respostas gravadas e o zip real).

## Decisões tomadas à mão

- **Rótulos da amostra de calibração** (`dados/rotulagem.csv`): as 50 foram rotuladas por um agente de IA especializado, com uma skill para questões jurídicas, com a justificativa de cada uma em `observacao`. Não houve especialista humano em Direito (ADR 0006). Limitações declaradas: o gabarito da calibração é de um modelo, e os 50 rótulos saíram da lista de candidatos da planilha, que sempre contém os Nós votados pelo pipeline. As duas coisas puxam a Precisão prevista para cima.
- _A completar ao longo da execução._

## Modelos, custo e tempo

**DeepSeek (Verificador e Juiz), painel de uso da conta em 18/10/2026:** US$ 3,04 em 439 requisições e 6.475.840 tokens. O número é acumulado desde a primeira chamada: inclui os testes de fumaça e as reclassificações. A rodada responde por 420 dessas requisições (359 do Verificador e 61 do Juiz, que só entra nos desacordos), e a reclassificação da Q0030 e da Q0099 depois da limpeza (ADR 0005) por mais 2.

| | Valor |
|---|---|
| Custo por requisição | US$ 0,0069 |
| Tokens por requisição | ~14,8 mil (a Árvore de temas inteira vai no system prompt) |
| Requisições por Questão | 1,17 (o Juiz em 17% delas) |
| Custo DeepSeek por Questão | até US$ 0,0085 (teto: divide o total, testes incluídos, pelas 359) |

**Embeddings (`gemini-embedding-2`):** cota gratuita do Gemini, sem custo. O que limita é a cota: 100 textos por minuto e um teto diário. Uma rodada de `sinais` vetoriza cerca de 730 textos (359 Questões e 371 Nós).

**Classificador (`claude -p` com `sonnet`, assinatura Claude Code):** não gera cobrança por chamada. O `claude -p` informa um custo equivalente ao preço da API: US$ 5,84 no piloto de 30 Questões (~5 min), ou US$ 0,19 por Questão. É mais de 20 vezes o custo da DeepSeek por Questão, e é o que pesa na projeção para produção (relatório, seção c).
