from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

UF_CHOICES = [
    ("AC", "AC"), ("AL", "AL"), ("AP", "AP"), ("AM", "AM"), ("BA", "BA"),
    ("CE", "CE"), ("DF", "DF"), ("ES", "ES"), ("GO", "GO"), ("MA", "MA"),
    ("MT", "MT"), ("MS", "MS"), ("MG", "MG"), ("PA", "PA"), ("PB", "PB"),
    ("PR", "PR"), ("PE", "PE"), ("PI", "PI"), ("RJ", "RJ"), ("RN", "RN"),
    ("RS", "RS"), ("RO", "RO"), ("RR", "RR"), ("SC", "SC"), ("SP", "SP"),
    ("SE", "SE"), ("TO", "TO"),
]


class Empresa(models.Model):
    cnpj = models.CharField("CNPJ", max_length=18, blank=True, null=True)
    nome_fantasia = models.CharField("Nome fantasia", max_length=255)
    razao_social = models.CharField("Razão social", max_length=255, blank=True, null=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    email = models.EmailField("E-mail", blank=True, null=True)
    site = models.URLField("Site", blank=True, null=True)

    cep = models.CharField("CEP", max_length=9, blank=True, null=True)
    logradouro = models.CharField("Logradouro", max_length=255, blank=True, null=True)
    numero = models.CharField("Número", max_length=20, blank=True, null=True)
    complemento = models.CharField("Complemento", max_length=255, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100, blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True, null=True)
    uf = models.CharField("UF", max_length=2, blank=True, null=True, choices=UF_CHOICES)

    observacao = models.TextField("Observações", blank=True, null=True)

    logo = models.ImageField("Logo", upload_to="logos/", blank=True, null=True)
    tema = models.CharField("Tema", max_length=50, blank=True, null=True)

    # Textos padrão das propostas
    exclusoes_padrao = models.TextField("Exclusões padrão", blank=True, null=True)
    declaracoes_padrao = models.TextField("Declarações padrão", blank=True, null=True)
    termo_confidencialidade_padrao = models.TextField("Termo de confidencialidade padrão", blank=True, null=True)
    prazo_inicio_padrao = models.CharField("Prazo de início padrão", max_length=100, blank=True, null=True)
    prazo_entrega_padrao = models.CharField("Prazo de entrega padrão", max_length=100, blank=True, null=True)
    agradecimentos_padrao = models.TextField("Agradecimentos padrão", blank=True, null=True)
    papel_timbrado = models.FileField("Papel timbrado", upload_to="papel_timbrado/", blank=True, null=True)

    ativo = models.BooleanField("Ativo", default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nome_fantasia"]

    def __str__(self):
        return self.nome_fantasia


class User(AbstractUser):
    """
    Usuário simplificado:
    - Vinculado a uma empresa
    - Tipo: owner (Administrador / Proprietário) ou normal (Usuário padrão)
    - Permissões: contatos, serviços, definições, propostas, usuários
    """

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="usuarios",
        null=True,
        blank=True,
    )

    USER_TYPE_CHOICES = [
        ("owner", "Administrador / Proprietário"),
        ("normal", "Usuário padrão"),
    ]
    user_type = models.CharField(
        "Tipo de usuário",
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="normal",
    )

    can_manage_contatos = models.BooleanField("Pode gerenciar contatos", default=True)
    can_manage_servicos = models.BooleanField("Pode gerenciar serviços", default=True)
    can_manage_definicoes = models.BooleanField("Pode alterar definições da empresa", default=False)
    can_manage_propostas_definicoes = models.BooleanField("Pode alterar definições de propostas", default=False)
    can_manage_propostas = models.BooleanField("Pode gerenciar propostas", default=False)
    can_manage_usuarios = models.BooleanField("Pode gerenciar usuários", default=False)

    def is_owner(self) -> bool:
        return self.user_type == "owner"


class Contato(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="contatos",
        verbose_name="Empresa",
    )

    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=20, blank=True, null=True)

    nome_fantasia = models.CharField(
        "Nome do cliente / Nome fantasia",
        max_length=255,
    )
    razao_social = models.CharField(
        "Razão social",
        max_length=255,
        blank=True,
        null=True,
    )

    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    email = models.EmailField("E-mail do contato", blank=True, null=True)
    ativo = models.BooleanField("Ativo", default=True)

    cep = models.CharField("CEP", max_length=9, blank=True, null=True)
    logradouro = models.CharField("Endereço", max_length=255, blank=True, null=True)
    numero = models.CharField("Número", max_length=20, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100, blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True, null=True)
    uf = models.CharField("UF", max_length=2, blank=True, null=True, choices=UF_CHOICES)
    complemento = models.CharField("Complemento", max_length=255, blank=True, null=True)

    is_cliente = models.BooleanField("Cliente", default=True)
    is_fornecedor = models.BooleanField("Fornecedor", default=False)
    is_parceiro = models.BooleanField("Parceiro", default=False)
    is_funcionario = models.BooleanField("Funcionário", default=False)
    is_responsavel_tecnico = models.BooleanField("Responsável técnico", default=False)
    is_outro = models.BooleanField("Outros", default=False)

    observacao = models.TextField("Observações", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        ordering = ["nome_fantasia"]

    def __str__(self):
        return self.nome_fantasia

    def get_relacionamentos_display(self):
        rels = []
        if self.is_cliente:
            rels.append("cliente")
        if self.is_fornecedor:
            rels.append("fornecedor")
        if self.is_parceiro:
            rels.append("parceiro")
        if self.is_funcionario:
            rels.append("funcionario")
        if self.is_responsavel_tecnico:
            rels.append("responsavel_tecnico")
        if self.is_outro:
            rels.append("outro")
        return rels


class CategoriaServico(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="categorias_servico",
        verbose_name="Empresa",
    )
    nome = models.CharField("Nome da categoria", max_length=100)

    class Meta:
        verbose_name = "Categoria de serviço"
        verbose_name_plural = "Categorias de serviço"
        ordering = ["nome"]
        unique_together = ("empresa", "nome")

    def __str__(self):
        return self.nome


class Servico(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="servicos",
        verbose_name="Empresa",
    )

    descricao = models.CharField("Descrição do serviço", max_length=255)

    categoria = models.ForeignKey(
        CategoriaServico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="servicos",
        verbose_name="Categoria",
    )

    entregaveis = models.TextField("Entregáveis", blank=True, null=True)
    ativo = models.BooleanField("Ativo", default=True)

    valor = models.DecimalField(
        "Valor padrão",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        help_text="Valor padrão sugerido nas propostas (editável lá).",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["descricao"]

    def __str__(self):
        return self.descricao


class PropostaConfiguracao(models.Model):
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        related_name="proposta_config",
    )

    exclusoes = models.TextField("Exclusões", blank=True)
    declaracoes = models.TextField("Declarações", blank=True)
    termo_confi = models.TextField("Termo de confidencialidade", blank=True)
    agradecimentos = models.TextField("Agradecimentos", blank=True)

    papel_timbrado = models.FileField(
        upload_to="propostas/papel_timbrado/",
        blank=True,
        null=True,
    )

    prazo_inicio = models.CharField(
        "Prazo para início dos serviços",
        blank=True,
    )
    prazo_entrega = models.CharField(
        "Prazo para entrega dos serviços",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Numeração automática
    numero_auto_iniciar = models.IntegerField(
        default=1,
        help_text="Valor inicial do contador automático de propostas.",
    )

    # Configuração visual (linhas com prefixo / parâmetro / sufixo)
    numero_config = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "Configuração visual de numeração automática "
            "(lista de linhas com prefixo, parâmetro e sufixo)."
        ),
    )

    # Margens internas do texto no PDF (em mm)
    margem_superior = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=20.0,
        help_text="Margem superior do texto no PDF (mm).",
    )
    margem_inferior = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=20.0,
        help_text="Margem inferior do texto no PDF (mm).",
    )
    margem_esquerda = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=15.0,
        help_text="Margem esquerda do texto no PDF (mm).",
    )
    margem_direita = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=15.0,
        help_text="Margem direita do texto no PDF (mm).",
    )

    class Meta:
        verbose_name = "Definições de propostas"
        verbose_name_plural = "Definições de propostas"

    def __str__(self):
        return f"Config. propostas - {self.empresa.nome_fantasia}"