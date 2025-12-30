// Propostas - JavaScript completo
// - Abas
// - CEP (ViaCEP)
// - Captação (modal + criação via AJAX)
// - Serviços (tabela de itens, apenas valor total)
// - Financeiro (subtotal, desconto, total)
// - Parcelamento (gerar parcelas, edição)
// - Finalização (objetivo, escopo, investimentos, textos padrão)
// - Alternar modelo próprio x modelo do sistema
// - Gerar número automático da proposta

(function () {
    "use strict";

    // ========================================================================
    // HELPERS
    // ========================================================================
    function formatMoney(value) {
        const v = Number(value || 0);
        return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    }

    function parseNumber(input) {
        if (typeof input === "number") return input;
        let s = String(input || "").trim();
        if (s === "") return 0;

        s = s.replace(/\s/g, "");
        if (s.indexOf(",") !== -1) {
            s = s.replace(/\./g, "").replace(/,/g, ".");
        } else {
            s = s.replace(/[^\d.\-]/g, "");
            const parts = s.split(".");
            if (parts.length > 2) {
                s = parts.shift() + "." + parts.join("");
            }
        }
        const n = Number(s);
        return isNaN(n) ? 0 : n;
    }

    function getCookie(name) {
        const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
        return v ? v.pop() : "";
    }

    function qId(id) {
        return document.getElementById(id);
    }

    // ========================================================================
    // MAIN INIT (executado na tela de proposta)
    // ========================================================================
    function mainInit() {
        const dataDiv = qId("propostaData");
        const captacaoCreateUrl = dataDiv ? dataDiv.dataset.captacaoCreateUrl : null;

        function safeParseFromData(attrName) {
            if (!dataDiv) return [];
            let raw = dataDiv.getAttribute(attrName) || "[]";
            try {
                return JSON.parse(raw);
            } catch (e1) {
                try {
                    const fixed = raw
                        .replace(/\\u0027/g, '"')
                        .replace(/'/g, '"')
                        .replace(/&quot;/g, '"');
                    return JSON.parse(fixed);
                } catch (e2) {
                    console.error(`Erro parse ${attrName}`, e2, "raw:", raw);
                    return [];
                }
            }
        }

        let itens = safeParseFromData("data-itens");
        let parcelas = safeParseFromData("data-parcelas");

        const form = qId("propostaForm");

        // --------------------------------------------------------------------
        // TABS
        // --------------------------------------------------------------------
        const tabs = document.querySelectorAll(".proposta-tab");
        const panels = document.querySelectorAll(".proposta-tab-panel");
        tabs.forEach((tab) => {
            tab.addEventListener("click", () => {
                const target = tab.getAttribute("data-tab");
                tabs.forEach((t) => t.classList.remove("active"));
                panels.forEach((p) => p.classList.remove("active"));
                tab.classList.add("active");
                const panel = document.querySelector(
                    `.proposta-tab-panel[data-tab="${target}"]`
                );
                if (panel) panel.classList.add("active");
            });
        });

        // --------------------------------------------------------------------
        // GERAR NÚMERO AUTOMÁTICO
        // --------------------------------------------------------------------
        const btnGerarNumero = qId("btnGerarNumeroProposta");
        const inputNumero = document.getElementById("id_numero");
        const urlGerarNumero = dataDiv ? dataDiv.dataset.gerarNumeroUrl : null;

        if (btnGerarNumero && inputNumero && urlGerarNumero) {
            btnGerarNumero.addEventListener("click", function () {
                btnGerarNumero.disabled = true;
                const originalText = btnGerarNumero.textContent;
                btnGerarNumero.textContent = "Gerando...";

                fetch(urlGerarNumero, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    credentials: "same-origin",
                })
                    .then((res) => res.json())
                    .then((data) => {
                        if (data.ok && data.numero) {
                            inputNumero.value = data.numero;
                        } else {
                            alert("Não foi possível gerar o número automático.");
                        }
                    })
                    .catch((err) => {
                        console.error("Erro ao gerar número automático:", err);
                        alert("Erro ao gerar o número automático.");
                    })
                    .finally(() => {
                        btnGerarNumero.disabled = false;
                        btnGerarNumero.textContent = originalText;
                    });
            });
        }

        // --------------------------------------------------------------------
        // CEP (ViaCEP)
        // --------------------------------------------------------------------
        const btnBuscarCep = qId("btnBuscarCep");
        const cepInput =
            document.getElementById("id_cep") ||
            document.querySelector('input[name="cep"]');
        const logInput =
            document.getElementById("id_logradouro") ||
            document.querySelector('input[name="logradouro"]');
        const numeroEndInput =
            document.getElementById("id_numero_end") ||
            document.querySelector('input[name="numero_end"]');
        const bairroInput =
            document.getElementById("id_bairro") ||
            document.querySelector('input[name="bairro"]');
        const cidadeInput =
            document.getElementById("id_cidade") ||
            document.querySelector('input[name="cidade"]');
        const ufInput =
            document.getElementById("id_uf") ||
            document.querySelector('select[name="uf"], input[name="uf"]');

        if (btnBuscarCep) {
            btnBuscarCep.addEventListener("click", async (e) => {
                e.preventDefault();
                const cep = (cepInput?.value || "").replace(/\D/g, "");
                if (!cep || cep.length !== 8) {
                    alert("Informe um CEP válido com 8 dígitos.");
                    cepInput?.focus();
                    return;
                }
                try {
                    btnBuscarCep.disabled = true;
                    const resp = await fetch(
                        `https://viacep.com.br/ws/${cep}/json/`
                    );
                    const data = await resp.json();
                    if (data.erro) {
                        alert("CEP não encontrado.");
                        return;
                    }
                    if (logInput) logInput.value = data.logradouro || "";
                    if (bairroInput) bairroInput.value = data.bairro || "";
                    if (cidadeInput) cidadeInput.value = data.localidade || "";
                    if (ufInput) ufInput.value = data.uf || "";
                } catch (err) {
                    console.error("Erro ao buscar CEP:", err);
                    alert("Erro ao buscar CEP. Tente novamente.");
                } finally {
                    btnBuscarCep.disabled = false;
                }
            });
        }

        // --------------------------------------------------------------------
        // MODAL CAPTAÇÃO
        // --------------------------------------------------------------------
        const btnNovaCaptacao = qId("btnNovaCaptacao");
        const modalCaptacaoBackdrop = qId("modalCaptacaoBackdrop");
        const btnSalvarCaptacao = qId("btnSalvarCaptacao");
        const btnCancelarCaptacao = qId("btnCancelarCaptacao");
        const captacaoNomeInput = qId("captacaoNome");
        const captacaoError = qId("captacaoError");
        const captacaoSelect =
            document.getElementById("id_captacao") ||
            document.querySelector('select[name="captacao"]');

        function showCaptacaoModal() {
            if (!modalCaptacaoBackdrop) return;
            modalCaptacaoBackdrop.style.display = "flex";
            modalCaptacaoBackdrop.setAttribute("aria-hidden", "false");
            if (captacaoNomeInput) {
                captacaoNomeInput.value = "";
                captacaoNomeInput.focus();
            }
            if (captacaoError) {
                captacaoError.classList.add("is-hidden");
                captacaoError.textContent = "";
            }
        }

        function hideCaptacaoModal() {
            if (!modalCaptacaoBackdrop) return;
            modalCaptacaoBackdrop.style.display = "none";
            modalCaptacaoBackdrop.setAttribute("aria-hidden", "true");
        }

        btnNovaCaptacao?.addEventListener("click", (e) => {
            e.preventDefault();
            showCaptacaoModal();
        });
        btnCancelarCaptacao?.addEventListener("click", (e) => {
            e.preventDefault();
            hideCaptacaoModal();
        });

        btnSalvarCaptacao?.addEventListener("click", async (e) => {
            e.preventDefault();
            const nome = (captacaoNomeInput?.value || "").trim();
            if (!nome) {
                if (captacaoError) {
                    captacaoError.classList.remove("is-hidden");
                    captacaoError.textContent = "Informe o nome da captação.";
                }
                return;
            }
            if (!captacaoCreateUrl) {
                if (captacaoError) {
                    captacaoError.classList.remove("is-hidden");
                    captacaoError.textContent =
                        "URL para criar captação indisponível.";
                }
                return;
            }
            try {
                btnSalvarCaptacao.disabled = true;
                btnSalvarCaptacao.textContent = "Salvando...";
                const formData = new FormData();
                formData.append("nome", nome);
                const resp = await fetch(captacaoCreateUrl, {
                    method: "POST",
                    headers: { "X-CSRFToken": getCookie("csrftoken") },
                    body: formData,
                    credentials: "same-origin",
                });
                const data = await resp.json();
                if (!resp.ok || !data.ok) {
                    const err =
                        data.error ||
                        `Erro ao criar captação (HTTP ${resp.status})`;
                    if (captacaoError) {
                        captacaoError.classList.remove("is-hidden");
                        captacaoError.textContent = err;
                    }
                    return;
                }
                if (captacaoSelect) {
                    let opt = captacaoSelect.querySelector(
                        `option[value="${data.id}"]`
                    );
                    if (!opt) {
                        opt = document.createElement("option");
                        opt.value = data.id;
                        opt.textContent = data.nome;
                        captacaoSelect.appendChild(opt);
                    }
                    captacaoSelect.value = String(data.id);
                }
                hideCaptacaoModal();
            } catch (err) {
                console.error("Erro criar captação", err);
                if (captacaoError) {
                    captacaoError.classList.remove("is-hidden");
                    captacaoError.textContent =
                        "Erro ao conectar. Tente novamente.";
                }
            } finally {
                btnSalvarCaptacao.disabled = false;
                btnSalvarCaptacao.textContent = "Salvar";
            }
        });

        if (modalCaptacaoBackdrop) {
            document.addEventListener("keydown", (e) => {
                if (
                    e.key === "Escape" &&
                    modalCaptacaoBackdrop.style.display === "flex"
                ) {
                    hideCaptacaoModal();
                }
            });
            modalCaptacaoBackdrop.addEventListener("click", (e) => {
                if (e.target === modalCaptacaoBackdrop) hideCaptacaoModal();
            });
        }

        // --------------------------------------------------------------------
        // SERVIÇOS (ITENS) – apenas valor total
        // --------------------------------------------------------------------
        const tabelaServicosBody = document.querySelector(
            "#tabelaServicos tbody"
        );
        const subtotalDisplay = qId("subtotalDisplay");
        const itensJsonInput = qId("itensJsonInput");
        const btnAdicionarServico = qId("btnAdicionarServico");
        const servicoSelect = qId("servicoSelect");

        function calcularSubtotal() {
            return itens.reduce((acc, it) => acc + parseNumber(it.valor), 0);
        }

        // --------------------------------------------------------------------
        // FINANCEIRO
        // --------------------------------------------------------------------
        const descontoModoSelect = qId("descontoModo");
        const descontoInput = qId("descontoInput");
        const finSubtotal = qId("finSubtotal");
        const finDesconto = qId("finDesconto");
        const finTotal = qId("finTotal");

        function calcularFinanceiro(subtotalForcado) {
            const subtotal =
                typeof subtotalForcado === "number"
                    ? subtotalForcado
                    : calcularSubtotal();

            const modo = descontoModoSelect?.value || "valor";
            const entrada = parseNumber(descontoInput?.value || 0);

            let desconto = 0;
            if (modo === "percentual") {
                let perc = entrada;
                if (perc < 0) perc = 0;
                if (perc > 100) perc = 100;
                desconto = subtotal * (perc / 100);
            } else {
                desconto = entrada;
            }
            if (desconto < 0) desconto = 0;
            if (desconto > subtotal) desconto = subtotal;

            const total = subtotal - desconto;

            if (finSubtotal)
                finSubtotal.textContent = formatMoney(subtotal);
            if (finDesconto)
                finDesconto.textContent = formatMoney(desconto);
            if (finTotal) finTotal.textContent = formatMoney(total);
            if (subtotalDisplay)
                subtotalDisplay.textContent = formatMoney(subtotal);

            return { subtotal, desconto, total };
        }

        function atualizarFinanceiro(subtotalForcado) {
            const res = calcularFinanceiro(subtotalForcado);
            atualizarResumoParcelas(res.total);
            renderInvestTabela();
            return res;
        }

        // --------------------------------------------------------------------
        // PARCELAMENTO
        // --------------------------------------------------------------------
        const parcelasQtdInput = qId("parcelasQtd");
        const parcelasTipoSelect = qId("parcelasTipo");
        const btnGerarParcelas = qId("btnGerarParcelas");
        const tabelaParcelasBody = document.querySelector(
            "#tabelaParcelas tbody"
        );
        const parcelasTotalSpan = qId("parcelasTotal");
        const parcelasDiferencaSpan = qId("parcelasDiferenca");
        const parcelasJsonInput = qId("parcelasJsonInput");

        function gerarMarco(tipo, index) {
            if (index === 0) return "Na autorização para início dos serviços";
            let dias = 0;
            switch (tipo) {
                case "mensal":
                    dias = 30 * index;
                    break;
                case "bimestral":
                    dias = 60 * index;
                    break;
                case "trimestral":
                    dias = 90 * index;
                    break;
                case "semestral":
                    dias = 180 * index;
                    break;
                case "anual":
                    dias = 365 * index;
                    break;
                case "unico":
                default:
                    dias = 0;
            }
            if (dias <= 0) return "Na autorização para início dos serviços";
            return `em ${dias} dias`;
        }

        function gerarParcelasAutomaticamente() {
            const { total } = atualizarFinanceiro();
            let qtd = parseInt(parcelasQtdInput?.value || "0", 10);
            if (isNaN(qtd) || qtd < 1) qtd = 1;
            if (qtd > 60) qtd = 60;

            const tipo = parcelasTipoSelect?.value || "unico";
            parcelas = [];

            if (qtd === 1) {
                parcelas.push({
                    numero: "1/1",
                    percentual: 100,
                    valor: total,
                    marco: gerarMarco(tipo, 0),
                });
            } else {
                const base = total / qtd;
                let soma = 0;
                for (let i = 0; i < qtd; i++) {
                    let valorParcela;
                    if (i === qtd - 1) {
                        valorParcela = total - soma;
                    } else {
                        valorParcela =
                            Math.round(base * 100) / 100;
                        soma += valorParcela;
                    }
                    const percentual =
                        total > 0 ? (valorParcela / total) * 100 : 0;
                    parcelas.push({
                        numero: `${i + 1}/${qtd}`,
                        percentual,
                        valor: valorParcela,
                        marco: gerarMarco(tipo, i),
                    });
                }
            }
            renderParcelas();
        }

        function atualizarResumoParcelas(totalForcado) {
            if (!parcelasTotalSpan || !parcelasDiferencaSpan) return;

            const total =
                typeof totalForcado === "number"
                    ? totalForcado
                    : atualizarFinanceiro().total;

            const somaParcelas = parcelas.reduce(
                (acc, p) => acc + parseNumber(p.valor),
                0
            );
            parcelasTotalSpan.textContent = formatMoney(somaParcelas);

            parcelasTotalSpan.className = "";
            parcelasDiferencaSpan.className = "";

            if (!total && !somaParcelas) {
                parcelasDiferencaSpan.textContent = "";
                parcelasDiferencaSpan.className = "text-muted";
                parcelasTotalSpan.className = "text-muted";
                return;
            }

            const diff = somaParcelas - total;
            const absDiff = Math.abs(diff);

            if (absDiff < 0.01) {
                parcelasDiferencaSpan.textContent =
                    " (igual ao total)";
                parcelasDiferencaSpan.className = "text-success";
                parcelasTotalSpan.className = "text-success";
                return;
            }

            const perc = total > 0 ? (absDiff / total) * 100 : 0;
            const sinal = diff > 0 ? "+" : "-";
            const situacao =
                diff > 0 ? "acima do total" : "abaixo do total";

            const texto = ` (${situacao}: ${sinal}${formatMoney(
                absDiff
            )} (${perc.toFixed(2)}%))`;

            parcelasDiferencaSpan.textContent = texto;

            if (diff > 0) {
                parcelasDiferencaSpan.className = "text-danger";
                parcelasTotalSpan.className = "text-danger";
            } else {
                parcelasDiferencaSpan.className = "text-warning";
                parcelasTotalSpan.className = "text-warning";
            }
        }

        function renderParcelas() {
            if (!tabelaParcelasBody) return;

            tabelaParcelasBody.innerHTML = "";
            const { total } = atualizarFinanceiro();

            parcelas.forEach((p, idx) => {
                const tr = document.createElement("tr");

                const tdParcela = document.createElement("td");
                tdParcela.textContent =
                    p.numero || `${idx + 1}/${parcelas.length}`;
                tr.appendChild(tdParcela);

                const tdPerc = document.createElement("td");
                const spanPerc = document.createElement("span");
                const valorAtual = parseNumber(p.valor);
                const perc =
                    total > 0 ? (valorAtual / total) * 100 : 0;
                p.percentual = perc;
                spanPerc.textContent = perc.toFixed(2) + "%";
                tdPerc.appendChild(spanPerc);
                tr.appendChild(tdPerc);

                const tdValor = document.createElement("td");
                const inputValor = document.createElement("input");
                inputValor.type = "number";
                inputValor.step = "0.01";
                inputValor.className = "form-control";
                inputValor.value = valorAtual.toFixed(2);
                inputValor.addEventListener("input", () => {
                    const novoValor =
                        Math.round(
                            parseNumber(inputValor.value) * 100
                        ) / 100;
                    p.valor = novoValor;

                    const novoPerc =
                        total > 0 ? (novoValor / total) * 100 : 0;
                    p.percentual = novoPerc;
                    spanPerc.textContent = novoPerc.toFixed(2) + "%";

                    if (parcelasJsonInput) {
                        parcelasJsonInput.value =
                            JSON.stringify(parcelas);
                    }
                    atualizarResumoParcelas(total);
                });
                tdValor.appendChild(inputValor);
                tr.appendChild(tdValor);

                const tdMarco = document.createElement("td");
                const inputMarco = document.createElement("input");
                inputMarco.type = "text";
                inputMarco.className = "form-control";
                inputMarco.value = p.marco || "";
                inputMarco.addEventListener("input", () => {
                    p.marco = inputMarco.value || "";
                    if (parcelasJsonInput) {
                        parcelasJsonInput.value =
                            JSON.stringify(parcelas);
                    }
                });
                tdMarco.appendChild(inputMarco);
                tr.appendChild(tdMarco);

                const tdVazio = document.createElement("td");
                tr.appendChild(tdVazio);

                tabelaParcelasBody.appendChild(tr);
            });

            if (parcelasJsonInput) {
                parcelasJsonInput.value = JSON.stringify(parcelas);
            }
            atualizarResumoParcelas(total);
        }

        // Eventos financeiro/parcelas
        descontoModoSelect?.addEventListener("change", () => {
            const res = atualizarFinanceiro();
            if (parcelas.length) renderParcelas();
            else atualizarResumoParcelas(res.total);
        });
        descontoInput?.addEventListener("input", () => {
            const res = atualizarFinanceiro();
            if (parcelas.length) renderParcelas();
            else atualizarResumoParcelas(res.total);
        });

        btnGerarParcelas?.addEventListener("click", (e) => {
            e.preventDefault();
            gerarParcelasAutomaticamente();
        });

        // --------------------------------------------------------------------
        // RENDER ITENS (tabela de serviços)
        // --------------------------------------------------------------------
        function renderItens() {
            if (!tabelaServicosBody) return;

            tabelaServicosBody.innerHTML = "";
            let subtotal = 0;

            itens.forEach((it, index) => {
                const tr = document.createElement("tr");

                const nomeTd = document.createElement("td");
                nomeTd.textContent = it.nome || "";
                tr.appendChild(nomeTd);

                const vtTd = document.createElement("td");
                const vtInput = document.createElement("input");
                vtInput.type = "number";
                vtInput.step = "0.01";
                vtInput.min = "0";
                vtInput.value =
                    it.valor != null
                        ? Number(it.valor).toFixed(2)
                        : "0.00";
                vtInput.className = "form-control";
                vtInput.addEventListener("input", () => {
                    it.valor =
                        Math.round(
                            parseNumber(vtInput.value) * 100
                        ) / 100;
                    it.quantidade = 1;
                    it.valor_unit = it.valor;
                    if (itensJsonInput)
                        itensJsonInput.value = JSON.stringify(itens);
                    const res = atualizarFinanceiro();
                    if (parcelas.length)
                        atualizarResumoParcelas(res.total);
                });
                vtTd.appendChild(vtInput);
                tr.appendChild(vtTd);

                const acaoTd = document.createElement("td");
                const btnDel = document.createElement("button");
                btnDel.type = "button";
                btnDel.className = "btn btn-danger btn-small";
                btnDel.textContent = "Remover";
                btnDel.addEventListener("click", () => {
                    itens.splice(index, 1);
                    renderItens();
                    const res = atualizarFinanceiro();
                    if (parcelas.length)
                        atualizarResumoParcelas(res.total);
                });
                acaoTd.appendChild(btnDel);
                tr.appendChild(acaoTd);

                tabelaServicosBody.appendChild(tr);
                subtotal += parseNumber(it.valor);
            });

            if (itensJsonInput)
                itensJsonInput.value = JSON.stringify(itens);
            atualizarFinanceiro(subtotal);
        }

        // Adicionar serviço de catálogo
        btnAdicionarServico?.addEventListener("click", () => {
            const opt = servicoSelect?.selectedOptions[0];
            if (!opt || !opt.value) {
                alert("Selecione um serviço para incluir.");
                return;
            }
            const id = Number(opt.value);
            const nome = opt.textContent.trim();
            const valorPadrao = parseNumber(opt.dataset.valor || 0);
            const entregaveis = opt.dataset.entregaveis || "";
            const valor = Math.round(valorPadrao * 100) / 100;

            itens.push({
                tipo: "catalogo",
                servico_id: id,
                nome,
                quantidade: 1,
                valor_unit: valor,
                valor: valor,
                entregaveis_texto: entregaveis,
            });
            servicoSelect.value = "";
            renderItens();
        });

        // --------------------------------------------------------------------
        // ITEM PERSONALIZADO (valor total)
        // --------------------------------------------------------------------
        const btnAddItemPersonalizado = qId("btnAddItemPersonalizado");
        const modalItem = qId("modalItemPersonalizado");
        const btnSalvarItemPersonalizado = qId("btnSalvarItemPersonalizado");
        const btnCancelarItemPersonalizado = qId("btnCancelarItemPersonalizado");

        const inputDescPers = qId("itemPersonalizadoDescricao");
        const inputVlrTotalPers = qId("itemPersonalizadoValorTotal");

        function abrirModalItem() {
            if (!modalItem) return;
            modalItem.style.display = "flex";
            if (inputDescPers) inputDescPers.value = "";
            if (inputVlrTotalPers) inputVlrTotalPers.value = "";
            inputDescPers?.focus();
        }

        function fecharModalItem() {
            if (!modalItem) return;
            modalItem.style.display = "none";
        }

        function salvarItemPersonalizado() {
            const desc = (inputDescPers?.value || "").trim();
            const vt = Number(inputVlrTotalPers?.value || 0);

            if (!desc) {
                alert("Informe a descrição do item.");
                inputDescPers?.focus();
                return;
            }
            if (!vt) {
                alert("Informe o valor total do item.");
                inputVlrTotalPers?.focus();
                return;
            }

            const novoItem = {
                tipo: "personalizado",
                nome: desc,
                quantidade: 1,
                valor_unit: vt,
                valor: vt,
            };

            itens.push(novoItem);
            renderItens();
            fecharModalItem();
        }

        btnAddItemPersonalizado?.addEventListener("click", (e) => {
            e.preventDefault();
            abrirModalItem();
        });
        btnSalvarItemPersonalizado?.addEventListener("click", (e) => {
            e.preventDefault();
            salvarItemPersonalizado();
        });
        btnCancelarItemPersonalizado?.addEventListener("click", (e) => {
            e.preventDefault();
            fecharModalItem();
        });
        if (modalItem) {
            modalItem.addEventListener("click", (e) => {
                if (e.target === modalItem) fecharModalItem();
            });
        }

        // --------------------------------------------------------------------
        // FINALIZAÇÃO – textos (objetivo, escopo, investimentos)
        // --------------------------------------------------------------------
        const objetivoTextarea = document.getElementById("objetivoTexto");
        const escopoTextarea = document.getElementById("escopoTexto");
        const investimentosTextarea = document.getElementById(
            "investimentosTexto"
        );
        const exibirApenasTotalCheckbox =
            document.getElementById("exibirApenasTotal");
        const btnGerarObjetivo = document.getElementById("btnGerarObjetivo");
        const btnGerarEscopo = document.getElementById("btnGerarEscopo");
        const btnGerarInvestimentos = document.getElementById(
            "btnGerarInvestimentos"
        );
        const investTabelaWrapper = document.getElementById(
            "investTabelaWrapper"
        );

        btnGerarObjetivo?.addEventListener("click", () => {
            const servicosNomes = itens
                .map((it) => it.nome)
                .filter(Boolean);
            const servicosTxt = servicosNomes.length
                ? servicosNomes.join(", ")
                : "[descrever serviços]";

            const partes = [];
            if (logInput?.value) partes.push(logInput.value);
            if (numeroEndInput?.value)
                partes.push(`Nº ${numeroEndInput.value}`);
            if (bairroInput?.value) partes.push(bairroInput.value);
            if (cidadeInput?.value) partes.push(cidadeInput.value);
            if (ufInput?.value) partes.push(ufInput.value);
            if (cepInput?.value) partes.push(cepInput.value);
            const endereco =
                partes.join(", ") || "[endereço da obra]";

            const texto = `A realização dos serviços: ${servicosTxt}, para o endereço: ${endereco}.`;
            if (objetivoTextarea) objetivoTextarea.value = texto;
        });

        btnGerarEscopo?.addEventListener("click", () => {
            if (!escopoTextarea) return;

            if (!itens.length) {
                escopoTextarea.value =
                    `2.1. [Nome do serviço]:
✓ [entregáveis do serviço]`;
                return;
            }

            const blocos = itens.map((it, idx) => {
                const indice = idx + 1;
                const nome = it.nome || `Serviço ${indice}`;

                let entregaveisRaw =
                    it.entregaveis_texto || "[entregáveis do serviço]";
                entregaveisRaw = entregaveisRaw.replace(
                    /&quot;/g,
                    '"'
                );
                entregaveisRaw = entregaveisRaw.replace(
                    /\\+n/g,
                    "\n"
                );

                const linhasEntregaveis = entregaveisRaw
                    .split(/\r?\n/)
                    .map((l) => l.trim())
                    .filter((l) => l.length > 0)
                    .map((l) => (l.startsWith("✓") ? l : `✓ ${l}`))
                    .join("\n");

                return `2.${indice}. ${nome}:\n${linhasEntregaveis}`;
            });

            escopoTextarea.value = blocos.join("\n\n");
        });

        function numeroPorExtensoSimples(total) {
            return formatMoney(total);
        }

        function renderInvestTabela() {
            if (!investTabelaWrapper) return;
            const { subtotal, desconto, total } = calcularFinanceiro();

            if (exibirApenasTotalCheckbox?.checked) {
                investTabelaWrapper.innerHTML =
                    `<p><strong>Total:</strong> ${formatMoney(
                        total
                    )}</p>`;
                return;
            }

            let rows = "";
            itens.forEach((it) => {
                rows += `
<tr>
  <td>${it.nome || "Serviço"}</td>
  <td class="right">${formatMoney(it.valor)}</td>
</tr>`;
            });
            if (!rows) {
                rows = `<tr><td colspan="2" class="text-muted center">Sem serviços adicionados</td></tr>`;
            }

            const descontoRow =
                desconto > 0
                    ? `<tr><td class="right">Desconto</td><td class="right">- ${formatMoney(
                        desconto
                    )}</td></tr>`
                    : "";

            investTabelaWrapper.innerHTML = `
<table class="table">
  <thead>
    <tr>
      <th>Serviço</th>
      <th class="right">Valor</th>
    </tr>
  </thead>
  <tbody>
    ${rows}
  </tbody>
  <tfoot>
    <tr>
      <td class="right"><strong>Subtotal</strong></td>
      <td class="right">${formatMoney(subtotal)}</td>
    </tr>
    ${descontoRow}
    <tr>
      <td class="right"><strong>Total</strong></td>
      <td class="right"><strong>${formatMoney(total)}</strong></td>
    </tr>
  </tfoot>
</table>`;
        }

        exibirApenasTotalCheckbox?.addEventListener(
            "change",
            renderInvestTabela
        );

        btnGerarInvestimentos?.addEventListener("click", () => {
            const { total } = calcularFinanceiro();

            let texto = "";
            const totalExtenso = numeroPorExtensoSimples(total);

            texto += `Pela elaboração dos serviços a CONTRATANTE pagará à CONTRATADA a importância de ${formatMoney(
                total
            )} (${totalExtenso}). O valor contratado deverá ser pago da seguinte maneira:\n\n`;

            if (!parcelas.length) {
                texto +=
                    "✓ [Definir forma de pagamento nas parcelas]\n";
            } else {
                parcelas.forEach((p, idx) => {
                    const valorParcela = parseNumber(p.valor);
                    const pct =
                        total > 0 ? (valorParcela / total) * 100 : 0;
                    const fracao =
                        p.numero || `${idx + 1}/${parcelas.length}`;
                    const marco = p.marco || "";
                    texto += `✓ (${fracao}) - ${formatMoney(
                        valorParcela
                    )} - (${pct.toFixed(
                        2
                    )}%) - ${marco}\n`;
                });
            }

            texto +=
                "\nObs.: Os valores apresentados poderão ser ajustados em comum acordo.\n";

            if (investimentosTextarea)
                investimentosTextarea.value = texto;
        });

        // --------------------------------------------------------------------
        // TEXTOS PADRÃO (resetar)
        // --------------------------------------------------------------------
        const exclusosTextarea = document.getElementById("exclusosTexto");
        const prazoInicioTextarea = document.getElementById(
            "prazoInicioTexto"
        );
        const prazoEntregaTextarea = document.getElementById(
            "prazoEntregaTexto"
        );
        const declaracoesTextarea = document.getElementById(
            "declaracoesTexto"
        );
        const confidencialidadeTextarea =
            document.getElementById("confidencialidadeTexto");
        const assinaturaTextarea = document.getElementById(
            "assinaturaTexto"
        );

        let defaults = {};
        if (dataDiv) {
            try {
                defaults = JSON.parse(
                    dataDiv.getAttribute("data-textos-padrao") ||
                    "{}"
                );
            } catch (e) {
                defaults = {};
            }
        }

        function resetTextarea(textarea, key) {
            if (!textarea || !defaults) return;
            const val = defaults[key] || "";
            textarea.value = val;
        }

        document
            .getElementById("btnResetExclusoes")
            ?.addEventListener("click", () => {
                resetTextarea(exclusosTextarea, "exclusos_texto");
            });
        document
            .getElementById("btnResetPrazoInicio")
            ?.addEventListener("click", () => {
                resetTextarea(
                    prazoInicioTextarea,
                    "prazo_inicio_texto"
                );
            });
        document
            .getElementById("btnResetPrazoEntrega")
            ?.addEventListener("click", () => {
                resetTextarea(
                    prazoEntregaTextarea,
                    "prazo_entrega_texto"
                );
            });
        document
            .getElementById("btnResetDeclaracoes")
            ?.addEventListener("click", () => {
                resetTextarea(
                    declaracoesTextarea,
                    "declaracoes_texto"
                );
            });
        document
            .getElementById("btnResetConfidencialidade")
            ?.addEventListener("click", () => {
                resetTextarea(
                    confidencialidadeTextarea,
                    "confidencialidade_texto"
                );
            });
        document
            .getElementById("btnResetAssinatura")
            ?.addEventListener("click", () => {
                resetTextarea(assinaturaTextarea, "assinatura_texto");
            });

        // --------------------------------------------------------------------
        // Alternar modelo próprio x modelo do sistema
        // --------------------------------------------------------------------
        const radiosModoFinalizacao = document.querySelectorAll(
            'input[name="usar_modelo_sistema"]'
        );
        const blocoAnexo = document.getElementById(
            "blocoFinalizacaoAnexo"
        );
        const blocoSistema = document.getElementById(
            "blocoFinalizacaoSistema"
        );

        function atualizarModoFinalizacao() {
            if (
                !radiosModoFinalizacao.length ||
                !blocoAnexo ||
                !blocoSistema
            )
                return;

            let selecionado = null;
            radiosModoFinalizacao.forEach((r) => {
                if (r.checked) selecionado = r;
            });
            if (!selecionado) return;

            const value = selecionado.value; // "0" ou "1"

            if (value === "0") {
                blocoAnexo.style.display = "";
                blocoSistema.style.display = "none";
            } else {
                blocoAnexo.style.display = "none";
                blocoSistema.style.display = "";
            }
        }

        atualizarModoFinalizacao();
        radiosModoFinalizacao.forEach((r) => {
            r.addEventListener("change", atualizarModoFinalizacao);
        });

        // --------------------------------------------------------------------
        // Render inicial e submit
        // --------------------------------------------------------------------
        renderItens();
        if (parcelas && parcelas.length) {
            renderParcelas();
        } else {
            atualizarResumoParcelas();
        }
        renderInvestTabela();

        if (form) {
            form.addEventListener("submit", () => {
                if (itensJsonInput)
                    itensJsonInput.value = JSON.stringify(itens || []);
                if (parcelasJsonInput)
                    parcelasJsonInput.value = JSON.stringify(
                        parcelas || []
                    );
                atualizarFinanceiro();
            });
        }
    }

    // Inicialização
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", mainInit);
    } else {
        mainInit();
    }
})();