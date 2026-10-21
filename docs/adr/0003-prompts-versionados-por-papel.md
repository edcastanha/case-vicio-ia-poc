# Prompts versionados por papel, com a versão gravada em cada voto

O Prompt de cada papel (Classificador, Verificador, Desempatador) fica num arquivo próprio, `prompts/v1/<papel>/<versao>.md`, e a versão ativa de cada papel é escolhida em `prompts/v1/versoes.toml` (ou por `<PAPEL>_PROMPT` no `.env`). Cada voto grava em `classificacoes.jsonl` o rótulo do prompt que o gerou, `papel/versao@hash`, em que o hash são os 8 primeiros dígitos do SHA-256 do texto. A entrega se recusa a calibrar uma rodada que misture versões do mesmo prompt ou que tenha votos sem versão.

O motivo é que a calibração mede um par (modelo, prompt): o limiar e a precisão prevista valem só para os textos que geraram os votos. Antes, os prompts eram constantes Python sem versão, e nada no resultado dizia qual texto tinha produzido cada voto. Mudar uma frase podia deixar metade da rodada num texto e metade em outro sem ninguém perceber.

Regras que decorrem disso:

- **Versão publicada não se edita.** Mudou o texto, é um arquivo novo (`v2.md`). `tests/v1/contrato/test_prompts_em_arquivo.py` fixa o hash de cada versão publicada, e o hash no rótulo pega a edição por fora dos testes.
- **Cada arquivo traz o texto inteiro do papel**, inclusive as regras comuns aos três. Repetir o texto é o preço de cada versão ser um retrato completo do que o modelo leu. Uma mudança nas regras comuns vira uma versão nova em cada papel afetado.
- **O Desempatador sozinho usa o prompt do Verificador** (Q42) e grava `verificador/<versao>@…`. Isso não conta como mistura, porque a checagem agrupa pelo prompt, e não pelo papel que votou.
- **O cache continua com chave no texto.** Uma versão nova não reaproveita respostas da anterior, e uma versão com texto idêntico reaproveita todas.

Em 18/10/2026, o papel Juiz passou a se chamar Desempatador, porque o nome sugere uma autoridade jurídica. A pasta virou `prompts/v1/desempatador/`, e os votos gravados passaram de `juiz/v1@c47bdf2d` para `desempatador/v1@c47bdf2d`. O texto não mudou, e por isso o hash é o mesmo, e a entrega gerada de novo saiu idêntica.

A v1 é byte a byte o texto das constantes que geraram a rodada completa: refazer as 359 Questões só pelo cache, com modelos proibidos de responder, reproduziu as 359 classificações gravadas, e por isso os votos antigos foram carimbados com a v1.

## Por que versionar, e o que isso nos dá

O raciocínio partiu da pergunta que guia o case: **o que torna a previsão de precisão verdadeira?** A previsão é uma afirmação sobre um sistema específico, e o prompt é parte desse sistema tanto quanto o modelo. Trocar o texto do Classificador muda o que ele erra, e portanto a Concordância, a pontuação e o limiar calibrado. Sem saber qual texto gerou cada voto, a previsão entregue é sobre um sistema que não dá para identificar.

Vantagens:

1. **Previsão rastreável.** `previsao.txt` vale para `classificador/v1@dce3cb01 + verificador/v1@7b8b74db + desempatador/v1@c47bdf2d` nos modelos declarados. Quem avaliar consegue ligar cada número da entrega ao texto exato que o produziu.
2. **Calibração protegida.** Rodada com versões misturadas não é calibrada. Sem essa trava, um ajuste de prompt no meio da rodada faria o limiar medir uma mistura de dois sistemas sem que ninguém percebesse.
3. **Experimentos comparáveis.** Testar uma v2 é criar um arquivo e rodar o piloto com `CLASSIFICADOR_PROMPT=v2`. A v1 continua intacta e o cache dela continua valendo, então comparar v1 com v2 no mesmo piloto custa só as chamadas da v2, e voltar atrás custa zero.
4. **Becos sem saída documentados.** O enunciado pede o caminho, inclusive o que foi descartado. Uma v2 que piorou continua no repositório com o motivo, em vez de sumir num histórico de edições.
5. **Prompt revisável por quem não programa.** Em Markdown, fora do Python, o Professor consegue ler e propor mudanças no texto que define o que é "assunto central" sem passar por código.
6. **Independência visível.** A independência entre Classificador e Verificador (ADR 0002) depende também de prompts diferentes. Arquivos separados por papel tornam isso explícito e evitam que alguém "unifique" os prompts e aproxime os erros dos dois.
7. **Pronto para produção.** A 50 mil Questões por semana, prompt é configuração com ciclo de vida: versão nova → piloto → recalibração na amostra auditada → troca da versão ativa. O rótulo em cada voto permite medir deriva e precisão por versão, e reverter trocando uma linha do `versoes.toml`.

O custo é baixo: um arquivo por versão e uma checagem na entrega. A migração não exigiu nenhuma chamada a modelo, porque a v1 reproduziu a rodada inteira pelo cache.

## Considered Options

- Versão no código (constantes `SISTEMA_CLASSIFICADOR_V2`): descartado, porque mistura texto jurídico com Python e dificulta que um Professor revise o prompt.
- Regras comuns num arquivo incluído pelos três: descartado, porque uma versão de papel deixaria de ser um texto fixo, e uma mudança no arquivo comum mudaria três versões em silêncio.
