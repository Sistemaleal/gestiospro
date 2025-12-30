document.addEventListener("DOMContentLoaded", () => {
  const btnNovaCategoria = document.getElementById("btn-nova-categoria");
  const categoriaSelect = document.querySelector('select[name="categoria"]');

  const modalBackdrop = document.getElementById("modal-categoria-backdrop");
  const modalInput = document.getElementById("nova-categoria-nome");
  const modalErro = document.getElementById("modal-categoria-erro");
  const btnModalCancelar = document.getElementById("modal-categoria-cancelar");
  const btnModalSalvar = document.getElementById("modal-categoria-salvar");

  // Se algum elemento essencial não existir, não faz nada
  if (
    !btnNovaCategoria ||
    !categoriaSelect ||
    !modalBackdrop ||
    !modalInput ||
    !modalErro ||
    !btnModalCancelar ||
    !btnModalSalvar
  ) {
    return;
  }

  function abrirModalCategoria() {
    modalErro.style.display = "none";
    modalErro.textContent = "";
    modalInput.value = "";
    modalBackdrop.style.display = "flex";
    modalInput.focus();
  }

  function fecharModalCategoria() {
    modalBackdrop.style.display = "none";
  }

  async function salvarCategoria() {
    const nome = modalInput.value.trim();
    if (!nome) {
      modalErro.textContent = "Informe o nome da categoria.";
      modalErro.style.display = "block";
      modalInput.focus();
      return;
    }

    try {
      const csrfInput = document.querySelector(
        '#servico-form input[name="csrfmiddlewaretoken"]'
      );
      const csrfToken = csrfInput ? csrfInput.value : "";

      const resp = await fetch("/servicos/categorias/nova/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: new URLSearchParams({ nome }),
      });

      if (!resp.ok) {
        let data = {};
        try {
          data = await resp.json();
        } catch (e) {
          // ignore
        }
        modalErro.textContent = data.error || "Erro ao criar categoria.";
        modalErro.style.display = "block";
        return;
      }

      const data = await resp.json();

      // adiciona opção se ainda não existir
      let option = categoriaSelect.querySelector(`option[value="${data.id}"]`);
      if (!option) {
        option = document.createElement("option");
        option.value = data.id;
        option.textContent = data.nome;
        categoriaSelect.appendChild(option);
      }

      // seleciona a nova categoria
      categoriaSelect.value = String(data.id);

      fecharModalCategoria();
    } catch (err) {
      console.error(err);
      modalErro.textContent = "Erro inesperado ao criar categoria.";
      modalErro.style.display = "block";
    }
  }

  // Eventos do botão principal
  btnNovaCategoria.addEventListener("click", (e) => {
    e.preventDefault();
    abrirModalCategoria();
  });

  // Eventos do modal
  btnModalCancelar.addEventListener("click", (e) => {
    e.preventDefault();
    fecharModalCategoria();
  });

  btnModalSalvar.addEventListener("click", (e) => {
    e.preventDefault();
    salvarCategoria();
  });

  // Fecha modal com ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalBackdrop.style.display === "flex") {
      fecharModalCategoria();
    }
  });

  // Fecha ao clicar fora do card
  modalBackdrop.addEventListener("click", (e) => {
    if (e.target === modalBackdrop) {
      fecharModalCategoria();
    }
  });
});