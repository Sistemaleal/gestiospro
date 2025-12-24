from decimal import Decimal, ROUND_HALF_UP
from django.db import models

import uuid
from django.utils import timezone

class Captacao(models.Model):
    company = models.ForeignKey(
        "core.Empresa",
        on_delete=models.CASCADE,
        related_name="captacoes",
    )
    nome = models.CharField(max_length=120)

    class Meta:
        ordering = ["nome"]
        unique_together = [("company", "nome")]

    def __str__(self) -> str:
        return self.nome


class Proposta(models.Model):
    STATUS_CHOICES = [
        ("rascunho", "Rascunho"),
        ("em_andamento", "Em andamento"),
        ("aprovado", "Aprovado"),
        ("rejeitado", "Rejeitado"),
        ("arquivado", "Arquivado"),
    ]

    company = models.ForeignKey(
        "core.Empresa",
        on_delete=models.CASCADE,
        related_name="propostas",
    )

    # Dados gerais
    numero = models.CharField(max_length=40)
    titulo_servico = models.CharField(max_length=180)
    data_servico = models.DateField(null=True, blank=True)  # Data da proposta
    validade = models.DateField(null=True, blank=True)

    captacao = models.ForeignKey(
        "propostas.Captacao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="propostas",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="rascunho",
    )

    cliente = models.ForeignKey(
        "core.Contato",
        on_delete=models.PROTECT,
        related_name="propostas",
    )

    # Endereço da obra
    cep = models.CharField(max_length=15, blank=True)
    logradouro = models.CharField(max_length=160, blank=True)
    numero_end = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=120, blank=True)
    cidade = models.CharField(max_length=120, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    complemento = models.CharField(max_length=160, blank=True)

    # Itens e Parcelas (JSON)
    itens = models.JSONField(default=list, blank=True)
    parcelas = models.JSONField(default=list, blank=True)

    DESCONTO_MODO = [
        ("valor", "Valor fixo"),
        ("percentual", "Percentual"),
    ]
    desconto_modo = models.CharField(
        max_length=12,
        choices=DESCONTO_MODO,
        default="valor",
    )
    desconto_input = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    desconto_valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    exibir_apenas_total = models.BooleanField(default=False)

    objetivo_texto = models.TextField(blank=True, default="")
    exclusos_texto = models.TextField(blank=True, default="")
    escopo_texto = models.TextField(blank=True, default="")          # <-- ADICIONAR
    investimentos_texto = models.TextField(blank=True, default="")  
    declaracoes_texto = models.TextField(blank=True, default="")
    confidencialidade_texto = models.TextField(blank=True, default="")
    assinatura_texto = models.TextField(blank=True, default="")
    prazo_inicio_texto = models.TextField(blank=True, default="")
    prazo_entrega_texto = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

# Link público
    public_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    permitir_acesso_publico = models.BooleanField(default=True)
    
# Rastreamento de resposta do cliente (opcional, mas útil)
    aprovado_em = models.DateTimeField(null=True, blank=True)
    rejeitado_em = models.DateTimeField(null=True, blank=True)
    revisao_solicitada_em = models.DateTimeField(null=True, blank=True)
    revisao_mensagem = models.TextField(blank=True, default="")

    # NOVO: controle de modelo de finalização
    usar_modelo_sistema = models.BooleanField(default=True)
    modelo_proprio_arquivo = models.FileField(
        upload_to="propostas/modelos_proprios/",
        null=True,
        blank=True,
        verbose_name="Modelo próprio de proposta",
    )

    # NOVO: sequência interna por empresa
    sequencia_int = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Sequência interna de numeração por empresa (1, 2, 3...).",
    )


    class Meta:
        unique_together = [("company", "numero")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.numero} • {self.titulo_servico}"

    def endereco_completo(self) -> str:
        partes = [
            self.logradouro or "",
            f"Nº {self.numero_end}" if self.numero_end else "",
            self.bairro or "",
            self.cidade or "",
            self.uf or "",
            self.cep or "",
        ]
        return ", ".join([p for p in partes if p])

    def calcular_totais(self):
        d = Decimal
        soma = d("0.00")
        for it in (self.itens or []):
            try:
                soma += d(str(it.get("valor") or "0"))
            except Exception:
                pass

        subtotal = soma.quantize(d("0.01"), rounding=ROUND_HALF_UP)

        entrada = d(str(self.desconto_input or "0"))
        if (self.desconto_modo or "valor") == "percentual":
            perc = max(d("0.00"), min(d("100.00"), entrada))
            desc_val = (subtotal * (perc / d("100"))).quantize(
                d("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            desc_val = max(d("0.00"), entrada)

        if desc_val > subtotal:
            desc_val = subtotal

        total = (subtotal - desc_val).quantize(
            d("0.01"),
            rounding=ROUND_HALF_UP,
        )

        self.subtotal = subtotal
        self.desconto_valor = desc_val
        self.total = total
        return subtotal, total