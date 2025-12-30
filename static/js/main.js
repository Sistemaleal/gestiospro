function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === "password") {
        input.type = "text";
        button.textContent = "Ocultar";
    } else {
        input.type = "password";
        button.textContent = "Mostrar";
    }
}

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('sidebar-collapsed');
}

// E no CSS, faça um modo só com ícone:
.sidebar - collapsed {
    width: 62px;
    min - width: 62px;
}
.sidebar - collapsed.sidebar - logo - text,
.sidebar - collapsed.sidebar - section - label,
.sidebar - collapsed.sidebar - item - label,
.sidebar - collapsed.sidebar - footer,
.sidebar - collapsed.sidebar - user - info {
    display: none;
}
.sidebar - collapsed.sidebar - logo - img - wrapper {
    margin - right: 0;
}
.sidebar - collapsed.sidebar - user - avatar {
    margin: 0 auto;
}