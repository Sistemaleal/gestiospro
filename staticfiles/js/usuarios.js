document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("id_password");
    const toggleBtn = document.getElementById("btn-toggle-password");

    if (passwordInput && toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const isPassword = passwordInput.type === "password";
            passwordInput.type = isPassword ? "text" : "password";
            toggleBtn.textContent = isPassword ? "Ocultar" : "Mostrar";
        });
    }
});