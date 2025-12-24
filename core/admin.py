from django.contrib import admin
from .models import Empresa, Contato, CategoriaServico, Servico


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "cnpj", "email", "telefone", "ativo")
    search_fields = ("nome_fantasia", "cnpj")
    list_filter = ("ativo",)


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "cpf_cnpj", "email", "telefone", "empresa", "ativo")
    list_filter = ("empresa", "ativo")
    search_fields = ("nome_fantasia", "cpf_cnpj", "email")


@admin.register(CategoriaServico)
class CategoriaServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa")
    list_filter = ("empresa",)
    search_fields = ("nome",)


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "categoria", "empresa", "ativo")
    list_filter = ("empresa", "categoria", "ativo")
    search_fields = ("descricao",)