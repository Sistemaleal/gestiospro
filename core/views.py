from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView

from .forms import (
    ContatoForm,
    ServicoForm,
    EmpresaForm,
    PropostaConfiguracaoForm,
    UserForm,  # ← ADICIONE ISTO
)

from .models import (
    Contato,
    Servico,
    Empresa,
    CategoriaServico,
    PropostaConfiguracao,
    User,
)

# =========================================================
# HELPERS DE PERMISSÃO / UTIL
# =========================================================

def user_has_empresa(user):
    return user.is_authenticated and getattr(user, "empresa", None) is not None


def user_can_manage_usuarios(user):
    return (
        user.is_authenticated
        and user_has_empresa(user)
        and (getattr(user, "user_type", "") == "owner" or getattr(user, "can_manage_usuarios", False))
    )


def user_can_manage_propostas(user):
    return (
        user.is_authenticated
        and user_has_empresa(user)
        and (getattr(user, "user_type", "") == "owner" or getattr(user, "can_manage_propostas", False))
    )


def user_can_manage_definicoes_propostas(user):
    return (
        user.is_authenticated
        and user_has_empresa(user)
        and (
            getattr(user, "user_type", "") == "owner"
            or getattr(user, "can_manage_propostas_definicoes", False)
        )
    )


# =========================================================
# HOME
# =========================================================

@login_required
def home(request):
    empresa = request.user.empresa
    return render(request, "core/home.html", {"empresa": empresa})


# =========================================================
# CONTATOS
# =========================================================

@method_decorator(login_required, name="dispatch")
class ContatoListView(ListView):
    model = Contato
    template_name = "core/contatos_list.html"
    context_object_name = "contatos"

    def get_queryset(self):
        return Contato.objects.filter(empresa=self.request.user.empresa)


@method_decorator(login_required, name="dispatch")
class ContatoCreateView(CreateView):
    model = Contato
    form_class = ContatoForm
    template_name = "core/contatos_form.html"
    success_url = reverse_lazy("core:contatos_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.request.user.empresa
        return kwargs

    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class ContatoUpdateView(UpdateView):
    model = Contato
    form_class = ContatoForm
    template_name = "core/contatos_form.html"
    success_url = reverse_lazy("core:contatos_list")

    def get_queryset(self):
        return Contato.objects.filter(empresa=self.request.user.empresa)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.request.user.empresa
        return kwargs


@login_required
def contato_delete(request, pk):
    contato = get_object_or_404(Contato, pk=pk, empresa=request.user.empresa)
    if request.method == "POST":
        nome = contato.nome_fantasia or contato.razao_social or contato.pk
        contato.delete()
        messages.success(request, f"Contato '{nome}' removido com sucesso.")
        return redirect("core:contatos_list")
    return render(request, "core/contatos_delete_confirm.html", {"contato": contato})


# =========================================================
# SERVIÇOS
# =========================================================

@method_decorator(login_required, name="dispatch")
class ServicoListView(ListView):
    model = Servico
    template_name = "core/servicos_list.html"
    context_object_name = "servicos"

    def get_queryset(self):
        return Servico.objects.filter(empresa=self.request.user.empresa)


@method_decorator(login_required, name="dispatch")
class ServicoCreateView(CreateView):
    model = Servico
    form_class = ServicoForm
    template_name = "core/servicos_form.html"
    success_url = reverse_lazy("core:servicos_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.request.user.empresa
        return kwargs

    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class ServicoUpdateView(UpdateView):
    model = Servico
    form_class = ServicoForm
    template_name = "core/servicos_form.html"
    success_url = reverse_lazy("core:servicos_list")

    def get_queryset(self):
        return Servico.objects.filter(empresa=self.request.user.empresa)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.request.user.empresa
        return kwargs


@login_required
def servico_delete(request, pk):
    servico = get_object_or_404(Servico, pk=pk, empresa=request.user.empresa)
    if request.method == "POST":
        descricao = servico.descricao
        servico.delete()
        messages.success(request, f"Serviço '{descricao}' removido com sucesso.")
        return redirect("core:servicos_list")
    return render(request, "core/servicos_delete_confirm.html", {"servico": servico})


@login_required
def categoria_servico_create_ajax(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido."}, status=405)

    nome = request.POST.get("nome", "").strip()
    if not nome:
        return JsonResponse({"error": "Informe o nome da categoria."}, status=400)

    categoria, created = CategoriaServico.objects.get_or_create(
        empresa=request.user.empresa,
        nome=nome,
    )

    return JsonResponse(
        {
            "id": categoria.id,
            "nome": categoria.nome,
            "created": created,
        }
    )

@login_required
def servico_valor_json(request, pk):
    servico = get_object_or_404(Servico, pk=pk, empresa=request.user.empresa)
    return JsonResponse({"valor": str(servico.valor or 0)})

# =========================================================
# DEFINIÇÕES DA EMPRESA
# =========================================================

@login_required
def definicoes_empresa(request):
    empresa = request.user.empresa
    if request.method == "POST":
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados da empresa atualizados com sucesso.")
            return redirect("core:definicoes_empresa")
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, "core/definicoes_empresa.html", {"form": form})


# =========================================================
# DEFINIÇÕES DE PROPOSTAS
# =========================================================

@login_required
def definicoes_propostas(request):
    if not user_can_manage_definicoes_propostas(request.user):
        return HttpResponseForbidden("Você não tem permissão para acessar esta página.")

    empresa = request.user.empresa
    config, _ = PropostaConfiguracao.objects.get_or_create(empresa=empresa)

    if request.method == "POST":
        form = PropostaConfiguracaoForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            config = form.save(commit=False)

            # Remover papel timbrado se marcado
            if request.POST.get("papel_timbrado_clear") == "on":
                if config.papel_timbrado:
                    config.papel_timbrado.delete(save=False)
                config.papel_timbrado = None

            # numero_config já foi setado no form.save()
            config.save()
            messages.success(request, "Definições de propostas atualizadas.")
            return redirect("core:definicoes_propostas")
    else:
        form = PropostaConfiguracaoForm(instance=config)

    return render(request, "core/definicoes_propostas.html", {"form": form})
    
# =========================================================
# PÁGINA EM BREVE GENÉRICA
# =========================================================

@login_required
def em_breve(request, secao):
    return render(request, "core/em_breve.html", {"secao": secao})


# =========================================================
# USUÁRIOS
# =========================================================

@login_required
def usuarios_list(request):
    if not user_can_manage_usuarios(request.user):
        messages.error(request, "Você não tem permissão para gerenciar usuários.")
        return redirect("core:home")

    usuarios = User.objects.filter(empresa=request.user.empresa).order_by("first_name", "username")
    return render(request, "core/usuarios_list.html", {"usuarios": usuarios})


@login_required
def usuarios_create(request):
    if not user_can_manage_usuarios(request.user):
        messages.error(request, "Você não tem permissão para gerenciar usuários.")
        return redirect("core:home")

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.empresa = request.user.empresa
            usuario.first_name = request.POST.get("first_name", "").strip()
            usuario.last_name = request.POST.get("last_name", "").strip()

            if usuario.user_type == "owner":
                usuario.can_manage_contatos = True
                usuario.can_manage_servicos = True
                usuario.can_manage_definicoes = True
                usuario.can_manage_propostas_definicoes = True
                usuario.can_manage_usuarios = True
                usuario.can_manage_propostas = True

            usuario.save()
            messages.success(request, "Usuário criado com sucesso.")
            return redirect("core:usuarios_list")
    else:
        form = UserForm()

    return render(request, "core/usuarios_form.html", {"form": form})


@login_required
def usuarios_update(request, pk):
    if not user_can_manage_usuarios(request.user):
        messages.error(request, "Você não tem permissão para gerenciar usuários.")
        return redirect("core:home")

    usuario = get_object_or_404(User, pk=pk, empresa=request.user.empresa)

    if usuario.user_type == "owner" and request.user.pk != usuario.pk:
        messages.error(request, "Somente o proprietário pode editar seus próprios dados.")
        return redirect("core:usuarios_list")

    if request.method == "POST":
        form = UserForm(request.POST, instance=usuario)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.first_name = request.POST.get("first_name", "").strip()
            obj.last_name = request.POST.get("last_name", "").strip()
            obj.save()
            messages.success(request, "Usuário atualizado com sucesso.")
            return redirect("core:usuarios_list")
    else:
        form = UserForm(instance=usuario)

    return render(request, "core/usuarios_form.html", {"form": form, "object": usuario})


@login_required
def usuarios_delete(request, pk):
    if not user_can_manage_usuarios(request.user):
        messages.error(request, "Você não tem permissão para gerenciar usuários.")
        return redirect("core:home")

    usuario = get_object_or_404(User, pk=pk, empresa=request.user.empresa)

    if usuario.user_type == "owner":
        messages.error(request, "O usuário proprietário não pode ser removido.")
        return redirect("core:usuarios_list")

    if request.user.pk == usuario.pk:
        messages.error(request, "Você não pode remover o próprio usuário.")
        return redirect("core:usuarios_list")

    if request.method == "POST":
        nome = usuario.get_full_name() or usuario.username
        usuario.delete()
        messages.success(request, f"Usuário '{nome}' removido com sucesso.")
        return redirect("core:usuarios_list")

    return render(request, "core/usuarios_delete_confirm.html", {"usuario": usuario})


@login_required
def contato_detail_json(request, pk):
    contato = get_object_or_404(Contato, pk=pk, empresa=request.user.empresa)
    nome = contato.nome_fantasia or contato.razao_social or ""
    email = contato.email or ""
    partes = nome.strip().split()
    first_name = partes[0] if partes else ""
    last_name = " ".join(partes[1:]) if len(partes) > 1 else ""
    return JsonResponse(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "nome_completo": nome,
        }
    )


