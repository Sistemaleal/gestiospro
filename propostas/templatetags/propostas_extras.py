from django import template

register = template.Library()

@register.filter
def br_currency(value):
    """
    Formata número como moeda brasileira: 2490 -> '2.490,00'
    Aceita int, float, Decimal ou string numérica.
    """
    if value is None or value == "":
        return ""
    try:
        valor = float(value)
    except (TypeError, ValueError):
        # Se não der pra converter em número, devolve como veio
        return value

    # Formata como 2,490.00 (padrão US)
    s = f"{valor:,.2f}"
    # Converte para 2.490,00
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s