// Helper para limpar caracteres não numéricos
function somenteNumeros(str) {
    return (str || "").replace(/\D/g, "");
}

async function buscarCNPJ() {
    const cnpjInput = document.querySelector('input[name="cpf_cnpj"]');
    if (!cnpjInput) return;

    let cnpj = somenteNumeros(cnpjInput.value);
    if (!cnpj) {
        alert("Informe o CNPJ para pesquisar.");
        return;
    }

    try {
        // endpoint base do seu VBA
        const url = `https://open.cnpja.com/office/${cnpj}`;

        const resp = await fetch(url, {
            headers: {
                Accept: "application/json",
            },
        });

        if (!resp.ok) {
            alert(`Erro ao consultar CNPJ: HTTP ${resp.status}`);
            return;
        }

        const data = await resp.json();

        // mapeamento básico seguindo sua lógica em VBA
        const razaoSocialInput = document.querySelector('input[name="razao_social"]');
        const nomeFantasiaInput = document.querySelector('input[name="nome_fantasia"]');
        const logradouroInput = document.querySelector('input[name="logradouro"]');
        const numeroInput = document.querySelector('input[name="numero"]');
        const bairroInput = document.querySelector('input[name="bairro"]');
        const cidadeInput = document.querySelector('input[name="cidade"]');
        const ufSelect = document.querySelector('select[name="uf"]');
        const cepInput = document.querySelector('input[name="cep"]');
        const telefoneInput = document.querySelector('input[name="telefone"]');
        const emailInput = document.querySelector('input[name="email"]');

        // company
        if (data.company) {
            if (razaoSocialInput) razaoSocialInput.value = data.company.name || "";
        }

        if (nomeFantasiaInput) {
            nomeFantasiaInput.value = data.alias || nomeFantasiaInput.value;
        }

        // endereço
        if (data.address) {
            if (logradouroInput) logradouroInput.value = data.address.street || "";
            if (numeroInput) numeroInput.value = data.address.number || "";
            if (bairroInput) bairroInput.value = data.address.district || "";
            if (cidadeInput) cidadeInput.value = data.address.city || "";
            if (cepInput) cepInput.value = data.address.zip || "";

            if (ufSelect && data.address.state) {
                ufSelect.value = data.address.state;
            }
        }

        // telefone (primeiro phones[0])
        if (Array.isArray(data.phones) && data.phones.length > 0 && telefoneInput) {
            const phone = data.phones[0];
            const area = phone.area || "";
            const numero = phone.number || "";
            telefoneInput.value = (area ? `(${area}) ` : "") + numero;
        }

        // email (primeiro emails[0])
        if (Array.isArray(data.emails) && data.emails.length > 0 && emailInput) {
            const emailObj = data.emails[0];
            emailInput.value = emailObj.address || "";
        }

        // foca no número
        if (numeroInput) {
            numeroInput.focus();
        }
    } catch (err) {
        console.error(err);
        alert("Erro inesperado ao consultar CNPJ.");
    }
}

async function buscarCEP() {
    const cepInput = document.querySelector('input[name="cep"]');
    if (!cepInput) return;

    const cep = somenteNumeros(cepInput.value);
    if (!cep) {
        alert("Informe o CEP para buscar o endereço.");
        return;
    }

    try {
        const url = `https://viacep.com.br/ws/${cep}/json/`;
        const resp = await fetch(url);

        if (!resp.ok) {
            alert(`Erro ao consultar CEP: HTTP ${resp.status}`);
            return;
        }

        const data = await resp.json();
        if (data.erro) {
            alert("CEP não encontrado.");
            return;
        }

        const logradouroInput = document.querySelector('input[name="logradouro"]');
        const bairroInput = document.querySelector('input[name="bairro"]');
        const cidadeInput = document.querySelector('input[name="cidade"]');
        const ufSelect = document.querySelector('select[name="uf"]');

        if (logradouroInput) logradouroInput.value = data.logradouro || "";
        if (bairroInput) bairroInput.value = data.bairro || "";
        if (cidadeInput) cidadeInput.value = data.localidade || "";

        if (ufSelect && data.uf) {
            ufSelect.value = data.uf;
        }

        const numeroInput = document.querySelector('input[name="numero"]');
        if (numeroInput) numeroInput.focus();
    } catch (err) {
        console.error(err);
        alert("Erro inesperado ao consultar CEP.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const btnCnpj = document.getElementById("btn-buscar-cnpj");
    const btnCep = document.getElementById("btn-buscar-cep");

    if (btnCnpj) {
        btnCnpj.addEventListener("click", (e) => {
            e.preventDefault();
            buscarCNPJ();
        });
    }

    if (btnCep) {
        btnCep.addEventListener("click", (e) => {
            e.preventDefault();
            buscarCEP();
        });
    }
});

// ===== Helpers =====
function somenteNumeros(str) {
    return (str || "").replace(/\D/g, "");
}

// ===== Máscaras =====
function maskCpfCnpj(value) {
    const v = somenteNumeros(value);
    if (v.length <= 11) {
        // CPF: 000.000.000-00
        return v
            .replace(/(\d{3})(\d)/, "$1.$2")
            .replace(/(\d{3})(\d)/, "$1.$2")
            .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    }
    // CNPJ: 00.000.000/0000-00
    return v
        .replace(/^(\d{2})(\d)/, "$1.$2")
        .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
        .replace(/\.(\d{3})(\d)/, ".$1/$2")
        .replace(/(\d{4})(\d)/, "$1-$2");
}

function maskTelefone(value) {
    let v = somenteNumeros(value);
    if (v.length > 11) v = v.slice(0, 11);

    if (v.length <= 10) {
        // (00) 0000-0000
        return v
            .replace(/^(\d{2})(\d)/, "($1) $2")
            .replace(/(\d{4})(\d)/, "$1-$2");
    }
    // (00) 00000-0000
    return v
        .replace(/^(\d{2})(\d)/, "($1) $2")
        .replace(/(\d{5})(\d)/, "$1-$2");
}

function maskCEP(value) {
    let v = somenteNumeros(value).slice(0, 8);
    return v.replace(/(\d{5})(\d)/, "$1-$2");
}

// ===== API: CNPJ =====
async function buscarCNPJ() {
    const cnpjInput = document.querySelector('input[name="cpf_cnpj"]');
    if (!cnpjInput) return;

    let cnpj = somenteNumeros(cnpjInput.value);
    if (!cnpj) {
        alert("Informe o CNPJ para pesquisar.");
        return;
    }

    try {
        const url = `https://open.cnpja.com/office/${cnpj}`;

        const resp = await fetch(url, {
            headers: {
                Accept: "application/json",
            },
        });

        if (!resp.ok) {
            alert(`Erro ao consultar CNPJ: HTTP ${resp.status}`);
            return;
        }

        const data = await resp.json();

        const razaoSocialInput = document.querySelector('input[name="razao_social"]');
        const nomeFantasiaInput = document.querySelector('input[name="nome_fantasia"]');
        const logradouroInput = document.querySelector('input[name="logradouro"]');
        const numeroInput = document.querySelector('input[name="numero"]');
        const bairroInput = document.querySelector('input[name="bairro"]');
        const cidadeInput = document.querySelector('input[name="cidade"]');
        const ufSelect = document.querySelector('select[name="uf"]');
        const cepInput = document.querySelector('input[name="cep"]');
        const telefoneInput = document.querySelector('input[name="telefone"]');
        const emailInput = document.querySelector('input[name="email"]');

        if (data.company && razaoSocialInput) {
            razaoSocialInput.value = data.company.name || "";
        }

        if (nomeFantasiaInput) {
            nomeFantasiaInput.value = data.alias || nomeFantasiaInput.value;
        }

        if (data.address) {
            if (logradouroInput) logradouroInput.value = data.address.street || "";
            if (numeroInput) numeroInput.value = data.address.number || "";
            if (bairroInput) bairroInput.value = data.address.district || "";
            if (cidadeInput) cidadeInput.value = data.address.city || "";
            if (cepInput) cepInput.value = maskCEP(data.address.zip || "");

            if (ufSelect && data.address.state) {
                ufSelect.value = data.address.state;
            }
        }

        if (Array.isArray(data.phones) && data.phones.length > 0 && telefoneInput) {
            const phone = data.phones[0];
            const area = phone.area || "";
            const numero = phone.number || "";
            telefoneInput.value = maskTelefone((area ? area : "") + numero);
        }

        if (Array.isArray(data.emails) && data.emails.length > 0 && emailInput) {
            const emailObj = data.emails[0];
            emailInput.value = emailObj.address || "";
        }

        if (numeroInput) {
            numeroInput.focus();
        }
    } catch (err) {
        console.error(err);
        alert("Erro inesperado ao consultar CNPJ.");
    }
}

// ===== API: CEP =====
async function buscarCEP() {
    const cepInput = document.querySelector('input[name="cep"]');
    if (!cepInput) return;

    const cep = somenteNumeros(cepInput.value);
    if (!cep) {
        alert("Informe o CEP para buscar o endereço.");
        return;
    }

    try {
        const url = `https://viacep.com.br/ws/${cep}/json/`;
        const resp = await fetch(url);

        if (!resp.ok) {
            alert(`Erro ao consultar CEP: HTTP ${resp.status}`);
            return;
        }

        const data = await resp.json();
        if (data.erro) {
            alert("CEP não encontrado.");
            return;
        }

        const logradouroInput = document.querySelector('input[name="logradouro"]');
        const bairroInput = document.querySelector('input[name="bairro"]');
        const cidadeInput = document.querySelector('input[name="cidade"]');
        const ufSelect = document.querySelector('select[name="uf"]');

        if (logradouroInput) logradouroInput.value = data.logradouro || "";
        if (bairroInput) bairroInput.value = data.bairro || "";
        if (cidadeInput) cidadeInput.value = data.localidade || "";
        if (ufSelect && data.uf) ufSelect.value = data.uf;

        const numeroInput = document.querySelector('input[name="numero"]');
        if (numeroInput) numeroInput.focus();
    } catch (err) {
        console.error(err);
        alert("Erro inesperado ao consultar CEP.");
    }
}

// ===== Inicialização =====
document.addEventListener("DOMContentLoaded", () => {
    const btnCnpj = document.getElementById("btn-buscar-cnpj");
    const btnCep = document.getElementById("btn-buscar-cep");

    if (btnCnpj) {
        btnCnpj.addEventListener("click", (e) => {
            e.preventDefault();
            buscarCNPJ();
        });
    }

    if (btnCep) {
        btnCep.addEventListener("click", (e) => {
            e.preventDefault();
            buscarCEP();
        });
    }

    // máscaras em tempo real
    const cpfCnpjInput = document.querySelector('input[name="cpf_cnpj"]');
    const telInput = document.querySelector('input[name="telefone"]');
    const cepInput = document.querySelector('input[name="cep"]');

    if (cpfCnpjInput) {
        cpfCnpjInput.addEventListener("input", () => {
            cpfCnpjInput.value = maskCpfCnpj(cpfCnpjInput.value);
        });
    }

    if (telInput) {
        telInput.addEventListener("input", () => {
            telInput.value = maskTelefone(telInput.value);
        });
    }

    if (cepInput) {
        cepInput.addEventListener("input", () => {
            cepInput.value = maskCEP(cepInput.value);
        });
    }
});