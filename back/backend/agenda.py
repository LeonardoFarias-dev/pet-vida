from datetime import date, datetime

# ==================================================
# HORÁRIOS E SERVIÇOS (fonte única para todo o projeto)
# ==================================================
HORARIOS = [
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
]

SERVICOS = [
    {"nome": "Banho", "icone": "🛁"},
    {"nome": "Tosa", "icone": "✂️"},
    {"nome": "Banho e Tosa", "icone": "🛁✂️"},
    {"nome": "Consulta", "icone": "🩺"},
]

NOMES_SERVICOS = [servico["nome"] for servico in SERVICOS]


def horarios_disponiveis(horarios, indisponiveis):
    """Devolve somente os horários que não estão na lista de indisponíveis."""
    return [
        horario
        for horario in horarios
        if horario not in indisponiveis
    ]


def horarios_passados(data_texto, horarios, agora=None):
    """
    Se a data for hoje, devolve os horários que já passaram.
    Para qualquer outra data devolve lista vazia.
    """
    agora = agora or datetime.now()

    if data_texto != agora.date().isoformat():
        return []

    hora_atual = agora.strftime("%H:%M")

    return [
        horario
        for horario in horarios
        if horario <= hora_atual
    ]


def data_valida(data_texto):
    """True se a data estiver no formato AAAA-MM-DD e não for anterior a hoje."""
    try:
        data = datetime.strptime(data_texto, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False

    return data >= date.today()
