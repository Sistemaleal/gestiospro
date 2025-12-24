import json
from datetime import date, datetime
from ast import literal_eval

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseForbidden,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from weasyprint import HTML, CSS

from .forms import PropostaDadosGeraisForm
from .models import Proposta, Captacao
from core.models import Servico, PropostaConfiguracao


# ======================================================================
# LISTA (KANBAN)
# ======================================================================
@login_required
def propostas_list(request):
    empresa = request.user.empresa

    busca = request.GET.get("q", "").strip()

    base_qs = Proposta.objects.filter(company=empresa)

    if busca:
        base_qs = base_qs.filter(
            Q(numero__icontains=busca)
            | Q(titulo_servico__icontains=busca)
            | Q(cliente__nome_fantasia__icontains=busca)
        )

    rascunhos = base_qs.filter(status="rascunho").order_by("-created_at")[:100]
    em_andamento = base_qs.filter(status="em_andamento").order_by("-updated_at")[:100]

    return render(
        request,
        "propostas/propostas_list.html",
        {
            "rascunhos": rascunhos,
            "em_andamento": em_andamento,
            "busca": busca,
        },
    )


# ======================================================================
# HISTÓRICO
# ======================================================================
@login_required
def propostas_historico(request):
    empresa = request.user.empresa

    status_hist = request.GET.get("status_hist", "aprovado")
    data_ini = request.GET.get("data_ini")
    data_fim = request.GET.get("data_fim")
    busca = request.GET.get("q", "").strip()

    base_qs = Proposta.objects.filter(company=empresa)

    if busca:
        base_qs = base_qs.filter(
            Q(numero__icontains=busca)
            | Q(titulo_servico__icontains=busca)
            | Q(cliente__nome_fantasia__icontains=busca)
        )

    historico_qs = base_qs.filter(status__in=["aprovado", "rejeitado", "arquivado"])

    if status_hist in ["aprovado", "rejeitado", "arquivado"]:
        historico_qs = historico_qs.filter(status=status_hist)

    if data_ini:
        historico_qs = historico_qs.filter(created_at__date__gte=data_ini)
    if data_fim:
        historico_qs = historico_qs.filter(created_at__date__lte=data_fim)

    historico_qs = historico_qs.order_by("-created_at")[:500]

    return render(
        request,
        "propostas/propostas_historico.html",
        {
            "historico": historico_qs,
            "status_hist": status_hist,
            "data_ini": data_ini or "",
            "data_fim": data_fim or "",
            "busca": busca,
        },
    )


# ======================================================================
# FUNÇÃO AUXILIAR PARA CORRIGIR JSONFIELD ANTIGO
# ======================================================================
def _fix_json_field(value):
    """
    Garante que o campo JSONField contenha uma lista/dict válida, e não
    uma string Python como "[{'a': 1}]".
    """
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        # tenta JSON normal
        try:
            v = json.loads(s)
            if isinstance(v, (list, dict)):
                return v
        except Exception:
            pass
        # tenta literal Python
        try:
            v = literal_eval(s)
            if isinstance(v, (list, dict)):
                return v
        except Exception:
            pass
    return []


# ======================================================================
# GERAÇÃO DE NÚMERO AUTOMÁTICO (sequencia_int por empresa)
# ======================================================================
def _gerar_numero_proposta(empresa):
    """
    Gera o número da proposta com base em:
    - PropostaConfiguracao.numero_auto_iniciar
    - PropostaConfiguracao.numero_config (linhas prefixo/param/sufixo)
    - Proposta.sequencia_int (sequência interna por empresa)

    Retorna (codigo, sequencia_int).
    """
    config = PropostaConfiguracao.objects.filter(empresa=empresa).first()

    # Próxima sequência interna da empresa (1, 2, 3...) baseada no maior sequencia_int
    agg = Proposta.objects.filter(company=empresa).aggregate(
        max_seq=Max("sequencia_int")
    )
    ultimo_seq = agg["max_seq"] or 0
    proxima_seq = ultimo_seq + 1

    # Se não houver configuração, usa apenas a sequência
    if not config:
        return str(proxima_seq), proxima_seq

    # numero interno: base + sequencia_int - 1
    base = config.numero_auto_iniciar or 1
    numero_interno = base + proxima_seq - 1

    agora = datetime.now()
    contexto_base = {
        "dia": f"{agora.day:02d}",
        "mes": f"{agora.month:02d}",
        "ano": str(agora.year),
        "horario": agora.strftime("%H%M"),
    }

    cfg = config.numero_config or []

    def montar_codigo(num):
        contexto = dict(contexto_base)
        contexto["numero"] = str(num)
        partes = []
        for linha in cfg:
            if not isinstance(linha, dict):
                continue
            prefixo = str(linha.get("prefixo", "") or "")
            param = str(linha.get("param", "") or "")
            sufixo = str(linha.get("sufixo", "") or "")
            valor_param = contexto.get(param, "") if param else ""
            partes.append(prefixo + valor_param + sufixo)
        codigo_local = "".join(partes).strip()
        if not codigo_local:
            codigo_local = str(num)
        return codigo_local

    # Loop de segurança: garante que o número gerado não exista ainda
    tentativas = 0
    max_tentativas = 1000
    numero_atual = numero_interno
    seq_atual = proxima_seq
    codigo = montar_codigo(numero_atual)

    while (
        Proposta.objects.filter(company=empresa, numero=codigo).exists()
        and tentativas < max_tentativas
    ):
        seq_atual += 1
        numero_atual = base + seq_atual - 1
        codigo = montar_codigo(numero_atual)
        tentativas += 1

    return codigo, seq_atual


@login_required
@require_POST
def proposta_gerar_numero(request):
    """
    Endpoint AJAX para botão "Gerar automático" na tela de proposta.
    Retorna apenas o código gerado para preencher o input do formulário.
    """
    empresa = request.user.empresa
    codigo, _ = _gerar_numero_proposta(empresa)
    return JsonResponse({"ok": True, "numero": codigo})


# ======================================================================
# CRIAÇÃO
# ======================================================================
@login_required
def proposta_create(request):
    empresa = request.user.empresa

    if request.method == "POST":
        form = PropostaDadosGeraisForm(request.POST, company=empresa)
        if form.is_valid():
            proposta = form.save(commit=False)
            proposta.company = empresa

            # Se número não foi informado, gera automático
            if not proposta.numero:
                codigo, seq = _gerar_numero_proposta(empresa)
                proposta.numero = codigo
                proposta.sequencia_int = seq

            # Itens / parcelas via JSON oculto
            itens_json = request.POST.get("itens_json") or "[]"
            parcelas_json = request.POST.get("parcelas_json") or "[]"
            try:
                proposta.itens = json.loads(itens_json)
            except json.JSONDecodeError:
                proposta.itens = []
            try:
                proposta.parcelas = json.loads(parcelas_json)
            except json.JSONDecodeError:
                proposta.parcelas = []

            # Financeiro
            proposta.desconto_modo = request.POST.get("desconto_modo", "valor")
            proposta.desconto_input = request.POST.get("desconto_input") or 0

            # Textos de finalização
            proposta.objetivo_texto = request.POST.get("objetivo_texto", "")
            proposta.escopo_texto = request.POST.get("escopo_texto", "")
            proposta.exclusos_texto = request.POST.get("exclusos_texto", "")
            proposta.declaracoes_texto = request.POST.get("declaracoes_texto", "")
            proposta.confidencialidade_texto = request.POST.get(
                "confidencialidade_texto", ""
            )
            proposta.assinatura_texto = request.POST.get("assinatura_texto", "")
            proposta.prazo_inicio_texto = request.POST.get("prazo_inicio_texto", "")
            proposta.prazo_entrega_texto = request.POST.get("prazo_entrega_texto", "")
            proposta.investimentos_texto = request.POST.get("investimentos_texto", "")
            proposta.exibir_apenas_total = bool(
                request.POST.get("exibir_apenas_total")
            )

            # Data da proposta: se não veio nada, define hoje
            if not proposta.data_servico:
                proposta.data_servico = date.today()

            # Calcular totais
            proposta.calcular_totais()
            proposta.save()
            messages.success(request, "Proposta criada com sucesso.")
            return redirect("propostas:proposta_edit", pk=proposta.pk)
    else:
        # GET: nova proposta
        form = PropostaDadosGeraisForm(company=empresa)

        # Data da proposta = hoje por padrão
        if not form.initial.get("data_servico"):
            form.initial["data_servico"] = date.today()

        # Textos padrão de PropostaConfiguracao / Empresa
        config = PropostaConfiguracao.objects.filter(empresa=empresa).first()

        exclusoes_padrao = ""
        declaracoes_padrao = ""
        termo_conf_padrao = ""
        prazo_inicio_padrao = ""
        prazo_entrega_padrao = ""
        agradecimentos_padrao = ""

        if config:
            exclusoes_padrao = config.exclusoes or ""
            declaracoes_padrao = config.declaracoes or ""
            termo_conf_padrao = config.termo_confi or ""
            prazo_inicio_padrao = config.prazo_inicio or ""
            prazo_entrega_padrao = config.prazo_entrega or ""
            agradecimentos_padrao = config.agradecimentos or ""

        if not exclusoes_padrao:
            exclusoes_padrao = empresa.exclusoes_padrao or ""
        if not declaracoes_padrao:
            declaracoes_padrao = empresa.declaracoes_padrao or ""
        if not termo_conf_padrao:
            termo_conf_padrao = empresa.termo_confidencialidade_padrao or ""
        if not prazo_inicio_padrao:
            prazo_inicio_padrao = empresa.prazo_inicio_padrao or ""
        if not prazo_entrega_padrao:
            prazo_entrega_padrao = empresa.prazo_entrega_padrao or ""
        if not agradecimentos_padrao:
            agradecimentos_padrao = empresa.agradecimentos_padrao or ""

        form.initial.setdefault("exclusos_texto", exclusoes_padrao)
        form.initial.setdefault("declaracoes_texto", declaracoes_padrao)
        form.initial.setdefault("confidencialidade_texto", termo_conf_padrao)
        form.initial.setdefault("prazo_inicio_texto", prazo_inicio_padrao)
        form.initial.setdefault("prazo_entrega_texto", prazo_entrega_padrao)
        form.initial.setdefault("assinatura_texto", agradecimentos_padrao)

    servicos = Servico.objects.filter(empresa=empresa, ativo=True).values(
        "id",
        "descricao",
        "valor",
        "entregaveis",
    )

    return render(
        request,
        "propostas/proposta_form.html",
        {
            "form": form,
            "proposta": None,
            "servicos": servicos,
        },
    )


# ======================================================================
# EDIÇÃO
# ======================================================================
@login_required
def proposta_edit(request, pk):
    empresa = request.user.empresa
    proposta = get_object_or_404(Proposta, pk=pk, company=empresa)

    # Corrigir itens/parcelas antigos salvos como string Python
    itens_fix = _fix_json_field(proposta.itens)
    parcelas_fix = _fix_json_field(proposta.parcelas)
    if itens_fix != proposta.itens or parcelas_fix != proposta.parcelas:
        proposta.itens = itens_fix
        proposta.parcelas = parcelas_fix
        proposta.save(update_fields=["itens", "parcelas"])

    if request.method == "POST":
        form = PropostaDadosGeraisForm(request.POST, instance=proposta, company=empresa)
        if form.is_valid():
            proposta = form.save(commit=False)

            # Itens / parcelas
            itens_json = request.POST.get("itens_json") or "[]"
            parcelas_json = request.POST.get("parcelas_json") or "[]"
            try:
                proposta.itens = json.loads(itens_json)
            except json.JSONDecodeError:
                proposta.itens = []
            try:
                proposta.parcelas = json.loads(parcelas_json)
            except json.JSONDecodeError:
                proposta.parcelas = []

            proposta.desconto_modo = request.POST.get("desconto_modo", "valor")
            proposta.desconto_input = request.POST.get("desconto_input") or 0

            # Textos finalização
            proposta.objetivo_texto = request.POST.get("objetivo_texto", "")
            proposta.escopo_texto = request.POST.get("escopo_texto", "")
            proposta.exclusos_texto = request.POST.get("exclusos_texto", "")
            proposta.declaracoes_texto = request.POST.get("declaracoes_texto", "")
            proposta.confidencialidade_texto = request.POST.get(
                "confidencialidade_texto", ""
            )
            proposta.assinatura_texto = request.POST.get("assinatura_texto", "")
            proposta.prazo_inicio_texto = request.POST.get("prazo_inicio_texto", "")
            proposta.prazo_entrega_texto = request.POST.get("prazo_entrega_texto", "")
            proposta.investimentos_texto = request.POST.get("investimentos_texto", "")
            proposta.exibir_apenas_total = bool(
                request.POST.get("exibir_apenas_total")
            )

            # modo de finalização (modelo próprio x sistema)
            usar_modelo_sistema_raw = request.POST.get("usar_modelo_sistema", "1")
            proposta.usar_modelo_sistema = usar_modelo_sistema_raw == "1"

            # arquivo do modelo próprio
            if not proposta.usar_modelo_sistema:
                arquivo = request.FILES.get("modelo_proprio_arquivo")
                if arquivo:
                    proposta.modelo_proprio_arquivo = arquivo
            else:
                # opcional: limpar arquivo quando volta pro sistema
                # proposta.modelo_proprio_arquivo = None
                pass

            proposta.calcular_totais()
            proposta.save()
            messages.success(request, "Proposta atualizada com sucesso.")
            return redirect("propostas:proposta_edit", pk=proposta.pk)
    else:
        form = PropostaDadosGeraisForm(instance=proposta, company=empresa)

    servicos = Servico.objects.filter(empresa=empresa, ativo=True).values(
        "id",
        "descricao",
        "valor",
        "entregaveis",
    )

    return render(
        request,
        "propostas/proposta_form.html",
        {
            "form": form,
            "proposta": proposta,
            "servicos": servicos,
        },
    )


# ======================================================================
# CAPTAÇÃO AJAX
# ======================================================================
@login_required
def captacao_create(request):
    """
    AJAX endpoint para criar Captacao direto da tela de proposta.
    Espera POST com 'nome'. Retorna JSON {ok: True, id, nome} ou erro.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método inválido."}, status=400)

    empresa = request.user.empresa
    nome = request.POST.get("nome", "").strip()
    if not nome:
        return JsonResponse({"ok": False, "error": "Nome é obrigatório."}, status=400)

    exists = Captacao.objects.filter(company=empresa, nome__iexact=nome).first()
    if exists:
        return JsonResponse({"ok": True, "id": exists.id, "nome": exists.nome})

    capt = Captacao.objects.create(company=empresa, nome=nome)
    return JsonResponse({"ok": True, "id": capt.id, "nome": capt.nome})


# ======================================================================
# PÚBLICA (VIEW + RESPOSTA CLIENTE)
# ======================================================================
def _get_proposta_publica_or_404(token):
    return get_object_or_404(
        Proposta,
        public_token=token,
        permitir_acesso_publico=True,
        company__isnull=False,
    )


def proposta_public_view(request, token):
    proposta = _get_proposta_publica_or_404(token)
    empresa = proposta.company

    itens = proposta.itens or []
    parcelas = proposta.parcelas or []

    return render(
        request,
        "propostas/proposta_publica.html",
        {
            "proposta": proposta,
            "empresa": empresa,
            "itens": itens,
            "parcelas": parcelas,
        },
    )


@csrf_exempt
def proposta_public_responder(request, token):
    """
    Endpoint público para registrar ação do cliente:
    - action = "aprovar" | "rejeitar" | "revisao"
    - mensagem (opcional, para revisão)
    """
    proposta = _get_proposta_publica_or_404(token)

    if request.method != "POST":
        return HttpResponseForbidden("Método inválido.")

    action = request.POST.get("action")
    mensagem = (request.POST.get("mensagem") or "").strip()
    agora = timezone.now()

    if action == "aprovar":
        proposta.status = "aprovado"
        proposta.aprovado_em = agora
        proposta.rejeitado_em = None
        proposta.revisao_solicitada_em = None
        proposta.revisao_mensagem = ""
        proposta.save(
            update_fields=[
                "status",
                "aprovado_em",
                "rejeitado_em",
                "revisao_solicitada_em",
                "revisao_mensagem",
            ]
        )
        msg = "Proposta aprovada com sucesso. Obrigado!"

    elif action == "rejeitar":
        proposta.status = "rejeitado"
        proposta.rejeitado_em = agora
        proposta.save(update_fields=["status", "rejeitado_em"])
        msg = "Proposta rejeitada. Obrigado pelo retorno."

    elif action == "revisao":
        proposta.status = "em_andamento"
        proposta.revisao_solicitada_em = agora
        proposta.revisao_mensagem = mensagem
        proposta.save(
            update_fields=["status", "revisao_solicitada_em", "revisao_mensagem"]
        )
        msg = "Seu pedido de revisão foi registrado. Entraremos em contato."

    else:
        return HttpResponseForbidden("Ação inválida.")

    return render(
        request,
        "propostas/proposta_publica_confirmacao.html",
        {
            "proposta": proposta,
            "mensagem": msg,
        },
    )


# ======================================================================
# PDF
# ======================================================================
@login_required
def proposta_public_pdf(request, pk):
    empresa = request.user.empresa
    proposta = get_object_or_404(Proposta, pk=pk, company=empresa)

    itens = _fix_json_field(proposta.itens)
    parcelas = _fix_json_field(proposta.parcelas)

    html_string = render_to_string(
        "propostas/proposta_publica_pdf.html",
        {
            "proposta": proposta,
            "empresa": empresa,
            "itens": itens,
            "parcelas": parcelas,
        },
        request=request,
    )

    base_url = request.build_absolute_uri("/")

    pdf_css = """
    @page {
        size: A4;
        margin: 20mm 15mm 20mm 15mm;
    }

    body.proposta-publica-pdf {
        margin: 0;
        padding: 0;
        font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
        background-color: #ffffff;
        color: #111827;
        font-size: 12pt;
        line-height: 1.5;
    }

    .header-pdf {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 4mm;
        margin-bottom: 6mm;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 3mm;
    }

    .header-esquerda {
        display: flex;
        align-items: center;
        gap: 8mm;
        flex: 1 1 60%;
        min-width: 0;
    }

    .empresa-logo {
        max-width: 25mm;
        max-height: 25mm;
        object-fit: contain;
    }

    .empresa-dados {
        font-size: 10pt;
        line-height: 1.2;
        overflow: hidden;
    }

    .empresa-dados p {
        margin: 0 0 2px 0;
        white-space: nowrap;
    }

    .empresa-nome {
        font-weight: 700;
        font-size: 12pt;
        margin: 0 0 3px 0;
    }

    .proposta-info {
        text-align: right;
        font-size: 10pt;
        line-height: 1.5;
        flex: 0 0 auto;
        min-width: 0;
        margin-top: 0;
    }

    .proposta-numero {
        font-weight: 700;
        font-size: 12pt;
        margin-bottom: 2px;
    }

    .conteudo-pdf {
        box-sizing: border-box;
    }

    .proposta-publica-section {
        page-break-inside: avoid;
        margin-top: 5mm;
    }

    .proposta-publica-section h2 {
        font-size: 14pt;
        margin: 0 0 2mm 0;
        font-weight: 700;
        text-transform: uppercase;
    }

    .proposta-publica-section h3 {
        font-size: 11pt;
        margin: 3mm 0 2mm 0;
        font-weight: 700;
        text-transform: uppercase;
    }

    .proposta-publica-section h4 {
        font-size: 11pt;
        margin: 2mm 0 1.5mm 0;
        font-weight: 600;
        text-transform: uppercase;
    }

    .proposta-publica-section p {
        margin: 0 0 1.5mm 0;
        white-space: pre-line;
        text-align: justify;
    }

    .proposta-publica-tabela {
        width: 100%;
        border-collapse: collapse;
        margin-top: 2mm;
        font-size: 10pt;
    }

    .proposta-publica-tabela th,
    .proposta-publica-tabela td {
        border: 1px solid #e5e7eb;
        padding: 3px 5px;
    }

    .proposta-publica-tabela thead th {
        background: #f3f4f6;
        font-weight: 600;
    }

    .right { text-align: right; }
    .center { text-align: center; }

    .assinatura-bloco {
        margin-top: 20mm;
        font-size: 12pt;
        text-align: center;
        height: 60mm;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        font-weight: 700;
    }

    .assinatura-linha {
        margin-top: 4mm;
        text-align: center;
        font-weight: 700;
    }
    """

    pdf_file = HTML(string=html_string, base_url=base_url).write_pdf(
        stylesheets=[CSS(string=pdf_css)]
    )

    response = HttpResponse(pdf_file, content_type="application/pdf")
    filename = f"Proposta_{proposta.numero}.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


# ======================================================================
# DELETE
# ======================================================================
@login_required
def proposta_delete(request, pk):
    empresa = request.user.empresa
    proposta = get_object_or_404(Proposta, pk=pk, company=empresa)

    if request.method == "POST":
        numero = proposta.numero
        proposta.delete()
        messages.success(request, f"Proposta {numero} excluída com sucesso.")
        return redirect("propostas:propostas_list")

    return redirect("propostas:proposta_edit", pk=pk)


# ======================================================================
# AÇÃO RÁPIDA: MUDAR STATUS (APROVAR / REJEITAR)
# ======================================================================
@login_required
@require_POST
def proposta_change_status(request, pk):
    """
    Ação rápida para marcar proposta como aprovada ou rejeitada a partir do Kanban.
    """
    empresa = request.user.empresa
    proposta = get_object_or_404(Proposta, pk=pk, company=empresa)

    novo_status = request.POST.get("status")
    if novo_status not in ["aprovado", "rejeitado"]:
        messages.error(request, "Status inválido.")
        return redirect("propostas:propostas_list")

    proposta.status = novo_status
    proposta.save(update_fields=["status"])

    if novo_status == "aprovado":
        messages.success(request, f"Proposta {proposta.numero} marcada como aprovada.")
    else:
        messages.success(request, f"Proposta {proposta.numero} marcada como rejeitada.")

    return redirect("propostas:propostas_list")