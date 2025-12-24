from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),

    # CONTATOS
    path("contatos/", views.ContatoListView.as_view(), name="contatos_list"),
    path("contatos/novo/", views.ContatoCreateView.as_view(), name="contatos_create"),
    path("contatos/<int:pk>/editar/", views.ContatoUpdateView.as_view(), name="contatos_update"),
    path("contatos/<int:pk>/remover/", views.contato_delete, name="contatos_delete"),

    # SERVIÇOS
    path("servicos/", views.ServicoListView.as_view(), name="servicos_list"),
    path("servicos/novo/", views.ServicoCreateView.as_view(), name="servicos_create"),
    path("servicos/<int:pk>/editar/", views.ServicoUpdateView.as_view(), name="servicos_update"),
    path("servicos/<int:pk>/remover/", views.servico_delete, name="servicos_delete"),

    # AJAX categoria de serviço
    path(
        "servicos/categorias/nova/",
        views.categoria_servico_create_ajax,
        name="servicos_categoria_create_ajax",
    ),

    path("servicos/<int:pk>/valor/", views.servico_valor_json, name="servico_valor_json"),
    
    # DEFINIÇÕES / EM BREVE
    path("definicoes/empresa/", views.definicoes_empresa, name="definicoes_empresa"),
    path("definicoes/propostas/", views.definicoes_propostas, name="definicoes_propostas"),

    path("em-breve/<str:secao>/", views.em_breve, name="em_breve"),
    
    # API simples para buscar dados de contato
    path("api/contatos/<int:pk>/", views.contato_detail_json, name="contato_detail_json"),
    
    path("usuarios/", views.usuarios_list, name="usuarios_list"),
    path("usuarios/novo/", views.usuarios_create, name="usuarios_create"),
    path("usuarios/<int:pk>/editar/", views.usuarios_update, name="usuarios_update"),
    path("usuarios/<int:pk>/remover/", views.usuarios_delete, name="usuarios_delete"),
]