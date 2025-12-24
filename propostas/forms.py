from django import forms
from django.core.exceptions import ValidationError

from .models import Proposta, Captacao
from core.models import Contato


# Lista de UFs do Brasil
UF_CHOICES = [
    ("", "Selecione..."),
    ("AC", "AC"), ("AL", "AL"), ("AP", "AP"), ("AM", "AM"),
    ("BA", "BA"), ("CE", "CE"), ("DF", "DF"), ("ES", "ES"),
    ("GO", "GO"), ("MA", "MA"), ("MT", "MT"), ("MS", "MS"),
    ("MG", "MG"), ("PA", "PA"), ("PB", "PB"), ("PR", "PR"),
    ("PE", "PE"), ("PI", "PI"), ("RJ", "RJ"), ("RN", "RN"),
    ("RS", "RS"), ("RO", "RO"), ("RR", "RR"), ("SC", "SC"),
    ("SP", "SP"), ("SE", "SE"), ("TO", "TO"),
]


class PropostaDadosGeraisForm(forms.ModelForm):
    uf = forms.ChoiceField(choices=UF_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        # empresa/empresa do usuário vem pela view
        self.empresa = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        # Filtra cliente/captação pela empresa
        if self.empresa:
            self.fields["cliente"].queryset = Contato.objects.filter(
                empresa=self.empresa,
                is_cliente=True,
            ).order_by("nome_fantasia")
            self.fields["captacao"].queryset = Captacao.objects.filter(
                company=self.empresa
            ).order_by("nome")

        # Forçar datas em formato ISO (YYYY-MM-DD) para inputs type="date"
        for field_name in ("data_servico", "validade"):
            field = self.fields.get(field_name)
            if not field:
                continue
            value = self.initial.get(field_name) or (
                self.instance and getattr(self.instance, field_name, None)
            )
            if value:
                # garante string "YYYY-MM-DD"
                self.initial[field_name] = value.strftime("%Y-%m-%d")

    def clean_numero(self):
        """
        Garante que não haja dois números de proposta iguais para a mesma empresa.
        """
        numero = self.cleaned_data.get("numero", "").strip()
        if not numero or not self.empresa:
            return numero

        qs = Proposta.objects.filter(company=self.empresa, numero=numero)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Já existe uma proposta com este número para esta empresa.")
        return numero

    class Meta:
        model = Proposta
        fields = [
            "numero",
            "titulo_servico",
            "data_servico",
            "validade",
            "captacao",
            "status",
            "cliente",
            "cep",
            "logradouro",
            "numero_end",
            "bairro",
            "cidade",
            "uf",
            "complemento",
        ]
        widgets = {
            "data_servico": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "validade": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

class PropostaFinalizacaoForm(forms.ModelForm):
    """
    Form para aba de Finalização:
    - controla se usa modelo do sistema ou modelo próprio
    - recebe o arquivo do modelo próprio
    - e todos os textos de finalização
    """

    # Vamos usar um TypedChoiceField só para lidar bem com "0"/"1" vindos dos radios
    usar_modelo_sistema = forms.TypedChoiceField(
        label="",
        choices=(
            (False, "Anexar meu modelo de proposta"),
            (True, "Usar modelo do sistema"),
        ),
        coerce=lambda v: v in ("1", "True", True),
        widget=forms.RadioSelect,
        required=False,
        initial=True,
    )

    class Meta:
        model = Proposta
        fields = [
            "usar_modelo_sistema",
            "modelo_proprio_arquivo",

            "objetivo_texto",
            "escopo_texto",
            "exclusos_texto",
            "investimentos_texto",
            "prazo_inicio_texto",
            "prazo_entrega_texto",
            "declaracoes_texto",
            "confidencialidade_texto",
            "assinatura_texto",
            "exibir_apenas_total",
        ]