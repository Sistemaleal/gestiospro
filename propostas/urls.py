from django.urls import path
from . import views

app_name = "propostas"

urlpatterns = [
    path("", views.propostas_list, name="propostas_list"),
    path("nova/", views.proposta_create, name="proposta_create"),
    path("<int:pk>/", views.proposta_edit, name="proposta_edit"),

    path("captacao/nova/", views.captacao_create, name="captacao_create"),

    path("p/<uuid:token>/", views.proposta_public_view, name="proposta_public_view"),
    path("p/<uuid:token>/responder/", views.proposta_public_responder, name="proposta_public_responder"),

    path("proposta/<int:pk>/pdf/", views.proposta_public_pdf, name="proposta_public_pdf"),

    path("", views.propostas_list, name="propostas_list"),
    path("historico/", views.propostas_historico, name="propostas_historico"),

    path("<int:pk>/excluir/", views.proposta_delete, name="proposta_delete"),
    path("<int:pk>/status/", views.proposta_change_status, name="proposta_change_status"),

    path("gerar-numero/", views.proposta_gerar_numero, name="proposta_gerar_numero"),
    
]