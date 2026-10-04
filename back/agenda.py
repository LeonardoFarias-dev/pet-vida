HORARIOS = [
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00"
]


def horarios_disponiveis(horarios, ocupados):

    return [
        horario
        for horario in horarios
        if horario not in ocupados
    ]


