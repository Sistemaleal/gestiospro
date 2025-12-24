from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

from core.models import Empresa, User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        # aqui usamos o campo padrão do Django: is_active
        if user is not None and user.is_active:
            login(request, user)
            next_url = request.GET.get("next") or "core:home"
            return redirect(next_url)
        else:
            messages.error(request, "Usuário ou senha inválidos, ou usuário inativo.")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


def registrar_empresa(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        nome_fantasia = request.POST.get("nome_fantasia")
        telefone = request.POST.get("telefone")
        email = request.POST.get("email")
        username = request.POST.get("username")
        senha = request.POST.get("senha")
        senha2 = request.POST.get("senha2")

        erros = []

        if not nome_fantasia:
            erros.append("Informe o Nome fantasia da empresa.")
        if not username:
            erros.append("Informe o nome de usuário.")
        if not senha:
            erros.append("Informe a senha.")
        if senha != senha2:
            erros.append("As senhas não conferem.")

        if User.objects.filter(username=username).exists():
            erros.append("Já existe um usuário com esse nome.")

        if erros:
            for e in erros:
                messages.error(request, e)
        else:
            empresa = Empresa.objects.create(
                nome_fantasia=nome_fantasia,
                telefone=telefone or "",
                email=email or "",
            )
            user = User.objects.create_user(
                username=username,
                email=email or "",
                password=senha,
                empresa=empresa,
                is_staff=True,
                is_superuser=False,
                user_type="owner",
                can_manage_contatos=True,
                can_manage_servicos=True,
                can_manage_definicoes=True,
                can_manage_usuarios=True,
                can_manage_propostas_definicoes=True,
            )
            
            messages.success(request, "Empresa e usuário criados com sucesso. Faça login.")
            return redirect("accounts:login")

    return render(request, "accounts/registrar_empresa.html")