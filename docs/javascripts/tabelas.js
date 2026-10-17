// Tabelas ordenáveis (receita do Material com tablesort), filtro da tabela de Questões e
// abertura do detalhe quando o link aponta para ele.
document$.subscribe(function () {
  document.querySelectorAll("article table:not([class])").forEach(function (tabela) {
    new Tablesort(tabela);
  });

  const filtro = document.getElementById("filtro-questoes");
  if (filtro) {
    const tabela = Array.from(document.querySelectorAll("article table")).find(function (t) {
      return filtro.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING;
    });
    filtro.addEventListener("input", function () {
      const termo = filtro.value.trim().toLowerCase();
      tabela.tBodies[0].querySelectorAll("tr").forEach(function (linha) {
        linha.hidden = termo !== "" && !linha.textContent.toLowerCase().includes(termo);
      });
    });
  }

  abrirDetalhe();
});

function abrirDetalhe() {
  const alvo = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (alvo && alvo.tagName === "DETAILS") {
    alvo.open = true;
    alvo.scrollIntoView();
  }
}

window.addEventListener("hashchange", abrirDetalhe);
