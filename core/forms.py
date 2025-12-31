from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import inlineformset_factory
import json

from .models import (
    Empresa,
    Contato,
    Servico,
    CategoriaServico,
    PropostaConfiguracao,
    User,
)


# =========================================================
# CONTATOS
# =========================================================

class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contato
        fields = [
            "cpf_cnpj",
            "nome_fantasia",
            "razao_social",
            "telefone",
            "email",
            "ativo",
            "cep",
            "logradouro",
            "numero",
            "bairro",
            "cidade",
            "uf",
            "complemento",
            "is_cliente",
            "is_fornecedor",
            "is_parceiro",
            "is_funcionario",
            "is_responsavel_tecnico",
            "is_outro",
            "observacao",
        ]
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        # se precisar filtrar algo por empresa, pode fazer aqui
        self.fields["nome_fantasia"].widget.attrs.setdefault("placeholder", "Nome do cliente")


# =========================================================
# SERVIÇOS
# =========================================================

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = [
            "descricao",
            "categoria",
            "entregaveis",
            "valor",
            "ativo",
        ]
        widgets = {
            "descricao": forms.TextInput(attrs={"placeholder": " "}),
            "categoria": forms.Select(),
            "entregaveis": forms.Textarea(attrs={"rows": 4}),
            "valor": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        if empresa is not None:
            self.fields["categoria"].queryset = CategoriaServico.objects.filter(
                empresa=empresa
            ).order_by("nome")
        else:
            self.fields["categoria"].queryset = CategoriaServico.objects.none()


# =========================================================
# EMPRESA
# =========================================================
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            "cnpj",
            "nome_fantasia",
            "razao_social",
            "telefone",
            "email",
            "site",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "observacao",
            "logo",
            "tema",
            "exclusoes_padrao",
            "declaracoes_padrao",
            "termo_confidencialidade_padrao",
            "prazo_inicio_padrao",
            "prazo_entrega_padrao",
            "agradecimentos_padrao",
            "papel_timbrado",
        ]
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 3}),
            "exclusoes_padrao": forms.Textarea(attrs={"rows": 3}),
            "declaracoes_padrao": forms.Textarea(attrs={"rows": 3}),
            "termo_confidencialidade_padrao": forms.Textarea(attrs={"rows": 3}),
            "agradecimentos_padrao": forms.Textarea(attrs={"rows": 3}),
            # ESSENCIAL: Usa FileInput simples, sem "Atualmente / Limpar"
            "logo": forms.FileInput(attrs={"id": "id_logo"}),
        }

# =========================================================
# DEFINIÇÕES DE PROPOSTA
# =========================================================

class PropostaConfiguracaoForm(forms.ModelForm):
    # Campo extra (hidden) usado pela UI de montagem para enviar o JSON
    numero_config_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = PropostaConfiguracao
        fields = [
            "exclusoes",
            "declaracoes",
            "termo_confi",
            "agradecimentos",
            "prazo_inicio",
            "prazo_entrega",
            "papel_timbrado",
            "margem_superior",
            "margem_inferior",
            "margem_esquerda",
            "margem_direita",
            "numero_auto_iniciar",
            # numero_config vem via numero_config_json
        ]
        widgets = {
            "exclusoes": forms.Textarea(attrs={"rows": 3}),
            "declaracoes": forms.Textarea(attrs={"rows": 3}),
            "termo_confi": forms.Textarea(attrs={"rows": 3}),
            "agradecimentos": forms.Textarea(attrs={"rows": 3}),
            "prazo_inicio": forms.TextInput(),
            "prazo_entrega": forms.TextInput(),
            "papel_timbrado": forms.FileInput(),
            "margem_superior": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "margem_inferior": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "margem_esquerda": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "margem_direita": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "numero_auto_iniciar": forms.NumberInput(attrs={"min": "1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Preenche o hidden com a config existente, se houver
        if self.instance and self.instance.numero_config:
            try:
                self.fields["numero_config_json"].initial = json.dumps(
                    self.instance.numero_config
                )
            except TypeError:
                self.fields["numero_config_json"].initial = "[]"

    def clean_numero_config_json(self):
        data = self.cleaned_data.get("numero_config_json") or ""
        if not data.strip():
            return []

        try:
            cfg = json.loads(data)
        except json.JSONDecodeError:
            raise forms.ValidationError("Configuração de numeração inválida.")

        if not isinstance(cfg, list):
            raise forms.ValidationError("Configuração de numeração inválida.")

        linhas_validas = []
        for item in cfg:
            if not isinstance(item, dict):
                continue

            prefixo = str(item.get("prefixo", "") or "")
            param = str(item.get("param", "") or "")
            sufixo = str(item.get("sufixo", "") or "")

            # ignora linhas totalmente vazias
            if not prefixo and not param and not sufixo:
                continue

            # se tiver param, verifica se é permitido
            if param and param not in {"dia", "mes", "ano", "horario", "numero"}:
                continue

            linhas_validas.append(
                {"prefixo": prefixo, "param": param, "sufixo": sufixo}
            )

        return linhas_validas

    def save(self, commit=True):
        instance = super().save(commit=False)

        # pega a lista validada em clean_numero_config_json
        cfg = self.cleaned_data.get("numero_config_json", [])
        instance.numero_config = cfg

        if commit:
            instance.save()
        return instance

# =========================================================
# USUÁRIOS
# =========================================================

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "user_type",
            "can_manage_contatos",
            "can_manage_servicos",
            "can_manage_usuarios",
            "can_manage_propostas",
            "can_manage_propostas_definicoes",
        ]