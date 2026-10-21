import subprocess
import sys

PROIBIDOS = [
    "classificacao.v2.adaptadores.claude_code",
    "classificacao.v2.adaptadores.embeddings_locais",
    "classificacao.v1",
    "sentence_transformers",
    "torch",
    "anthropic",
    "openai",
    "google.genai",
]


def test_o_caminho_da_entrega_v2_nao_carrega_nenhum_modelo_de_linguagem_nem_de_embeddings():
    codigo = (
        "import sys\n"
        "import classificacao.cli, classificacao.v2.entrada.cli, classificacao.v2.entrada.entrega\n"
        f"carregados = [m for m in {PROIBIDOS!r} if m in sys.modules]\n"
        "print(carregados)\n"
    )
    saida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    )
    assert saida.stdout.strip() == "[]"
