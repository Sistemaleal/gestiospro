from datetime import datetime

from django.db.models import Max

from core.models import PropostaConfiguracao
from .models import Proposta


def gerar_numero_proposta(empresa):
    """
    Gera um código de proposta com base em:
    - PropostaConfiguracao.numero_auto_iniciar
    - PropostaConfiguracao.numero_config
    - Proposta.sequencia_int (sequência interna por empresa)
    """

    config = PropostaConfiguracao.objects.filter(empresa=empresa).first()

    # Descobre a próxima sequência interna da empresa
    agg = Proposta.objects.filter(company=empresa).aggregate(
        max_seq=Max("sequencia_int")
    )
    ultimo_seq = agg["max_seq"] or 0
    proxima_seq = ultimo_seq + 1

    # Se não existir config, faz um fallback simples: só usa a sequência
    if not config:
        return str(proxima_seq)

    # Calcula o "numero" baseando-se na sequência e no numero_auto_iniciar
    base = config.numero_auto_iniciar or 1
    numero_interno = base + proxima_seq - 1

    agora = datetime.now()
    contexto = {
        "numero": str(numero_interno),
        "dia": f"{agora.day:02d}",
        "mes": f"{agora.month:02d}",
        "ano": str(agora.year),
        "horario": agora.strftime("%H%M"),
    }

    cfg = config.numero_config or []
    partes = []
    for linha in cfg:
        if not isinstance(linha, dict):
            continue
        prefixo = str(linha.get("prefixo", "") or "")
        param = str(linha.get("param", "") or "")
        sufixo = str(linha.get("sufixo", "") or "")
        valor_param = contexto.get(param, "") if param else ""
        partes.append(prefixo + valor_param + sufixo)

    codigo = "".join(partes).strip()
    if not codigo:
        codigo = str(numero_interno)

    return codigo, proxima_seq