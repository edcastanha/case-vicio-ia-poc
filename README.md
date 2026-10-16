# Classificação de tópicos — case Vício

Classifica 359 questões de Penal, Processo Penal, Legislação Penal Especial e Criminologia na árvore de temas da plataforma e decide, para cada uma, **publicar**, **revisar** ou **fora**, sob a régua de ≥ 95% de precisão nas publicadas. Enunciado: [`case-ia-classificacao-de-topicos.pdf`](case-ia-classificacao-de-topicos.pdf). Dados: [`anexos-case-ia.zip`](anexos-case-ia.zip) (lido direto, sem extrair).

## Como funciona, em uma frase por etapa

1. **Classificador** (Anthropic, `claude-sonnet-5-5`) escolhe o nó da árvore vendo a questão e a classificação de origem.
2. **Verificador** (Gemini, `gemini-3.8-flash`) escolhe de forma independente, **sem** ver a origem nem o Classificador.
3. **Juiz** (DeepSeek, `deepseek-v4-pro`) só entra quando os dois discordam, e só escolhe a sugestão que vai para o professor: **nunca publica**.
4. **Embeddings** (Gemini, `gemini-embedding-2`) dão um sinal extra (similaridade) e uma sugestão de reserva.
5. **Publica** só quem tem concordância de ramo entre dois provedores diferentes, nenhum modelo em dúvida, tema não duplicado e pontuação acima do limiar calibrado em uma amostra rotulada às cegas por um humano, mirando 97%.

As regras e o porquê de cada uma estão em [`docs/adr/`](docs/adr/); o vocabulário, em [`GLOSSARY.md`](GLOSSARY.md).

## Como rodar

Requer [uv](https://docs.astral.sh/uv/) e as três chaves de API.

```bash
uv sync
cp .env.example .env              # preencha as chaves
uv run pytest                     # testes (nenhum chama rede)

uv run classificacao rodada       # 1. classifica as 359 (retomável; cache em dados/cache)
uv run classificacao sinais       # 2. embeddings: similaridade e reserva
uv run classificacao amostra      # 3. gera dados/rotulagem.csv (50 questões, cega)
#                                   4. um humano preenche a coluna `resposta` (id do nó ou "nenhum")
uv run classificacao entrega      # 5. calibra nos rótulos e grava publicacao.csv e previsao.txt
```

O que gera o `publicacao.csv`: o passo 5, a partir de `dados/rodada/classificacoes.jsonl` (passo 1), `dados/rodada/sinais.json` (passo 2) e `dados/rotulagem.csv` (passos 3–4). Falhas de provedor vão para `dados/rodada/falhas.jsonl` e a questão termina em `revisar`; a entrega se recusa a gravar um arquivo fora do formato do LEIA-ME.

`uv run classificacao piloto --n 30` roda uma amostra; com `*_BACKEND=claude-code` no `.env` usa o `claude -p` local em vez das APIs (só para teste).

## Código

Clean Architecture em `src/classificacao/`, com dependências apontando para dentro:

| Camada | O que tem |
|---|---|
| `dominio/` | árvore e regra do ramo, decisão (publicar/revisar/fora), pontuação, calibração (limiar, bootstrap, curva), validação da entrega |
| `aplicacao/` | casos de uso (classificar questão, processar lote, sinais, amostra cega, calibração, entrega), portas e prompts |
| `adaptadores/` | Anthropic, Gemini, DeepSeek, `claude -p`, leitura do zip, planilha de rotulagem, cache/DLQ/registro em arquivo |
| `entrada/` | linha de comando e configuração por `.env` |

Testes em `tests/unit/` (regras, com fakes) e `tests/contrato/` (adaptadores, com respostas gravadas e o zip real).

## Decisões tomadas à mão

- **Rótulos da amostra de calibração** (`dados/rotulagem.csv`): preenchidos por um humano, às cegas, antes de ver as respostas dos modelos.
- _A completar ao longo da execução._

## Modelos, custo e tempo

_A completar com os números da rodada final._ Piloto de 30 questões no modo `claude-code`: ~5 min, custo equivalente informado pelo `claude -p` de US$ 5,84.
