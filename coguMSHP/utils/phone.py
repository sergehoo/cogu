import re


def nettoyer_numero(numero):
    if numero:
        return re.sub(r'\D', '', str(numero))
    return ""


def formater_numero_local(numero):
    numero = nettoyer_numero(numero)
    if len(numero) == 10:
        return f"{numero[:2]} {numero[2:4]} {numero[4:6]} {numero[6:8]} {numero[8:]}"
    elif len(numero) == 8:
        return f"{numero[:2]} {numero[2:4]} {numero[4:6]} {numero[6:]}"
    elif len(numero) > 10:
        return f"+{numero}"
    return numero
