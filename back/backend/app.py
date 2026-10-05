import os
import re
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    abort
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import conectar
from agenda import (
    HORARIOS,
    SERVICOS,
    NOMES_SERVICOS,
    horarios_disponiveis,
    horarios_passados,
    data_valida
)

# ==================================================
# CONFIGURAÇÃO DO FLASK
# ==================================================
app = Flask(
    __name__,
    static_folder="../front",
    static_url_path="/static"
)

# Em produção, defina a variável de ambiente PETVIDA_SECRET_KEY.
app.secret_key = os.environ.get(
    "PETVIDA_SECRET_KEY",
    "petvida-chave-secreta-troque-em-producao"
)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

ESPECIES = ["Cachorro", "Gato", "Outro"]

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MESES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]

ROTULOS_STATUS = {
    "confirmado": "Confirmado",
    "concluido": "Concluído",
    "cancelado": "Cancelado",
    "aguardando": "Aguardando",
    "notificado": "Horário liberado",
    "atendido": "Agendado"
}

EMOJIS_PET = {
    "Cachorro": "🐶",
    "Gato": "🐱",
    "Outro": "🐾"
}


# ==================================================
# FILTROS DO TEMPLATE (datas em português, etc.)
# ==================================================
@app.template_filter("data_br")
def data_br(valor):
    try:
        return datetime.strptime(
            str(valor)[:10], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
    except ValueError:
        return valor


@app.template_filter("datahora_br")
def datahora_br(valor):
    # O SQLite grava CURRENT_TIMESTAMP em UTC; Brasília = UTC-3.
    try:
        momento = datetime.strptime(
            str(valor)[:19], "%Y-%m-%d %H:%M:%S"
        ) - timedelta(hours=3)
        return momento.strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return valor


@app.template_filter("dia")
def filtro_dia(valor):
    try:
        return datetime.strptime(
            str(valor)[:10], "%Y-%m-%d"
        ).strftime("%d")
    except ValueError:
        return "--"


@app.template_filter("mes_abreviado")
def filtro_mes(valor):
    try:
        mes = datetime.strptime(
            str(valor)[:10], "%Y-%m-%d"
        ).month
        return MESES[mes - 1]
    except ValueError:
        return ""


@app.template_filter("rotulo_status")
def rotulo_status(valor):
    return ROTULOS_STATUS.get(valor, valor)


@app.template_filter("emoji_pet")
def emoji_pet(especie):
    return EMOJIS_PET.get(especie, "🐾")


@app.template_filter("icone_servico")
def icone_servico(nome):
    for servico in SERVICOS:
        if servico["nome"] == nome:
            return servico["icone"]
    return "🐾"


# ==================================================
# SEGURANÇA — CSRF
# ==================================================
def gerar_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


@app.before_request
def proteger_csrf():
    if request.method == "POST":
        enviado = request.form.get("csrf_token", "")
        esperado = session.get("csrf_token", "")

        if not esperado or not secrets.compare_digest(
            enviado, esperado
        ):
            abort(400)


# ==================================================
# VARIÁVEIS DISPONÍVEIS EM TODOS OS TEMPLATES
# ==================================================
@app.context_processor
def contexto_global():
    nao_lidas = 0

    if "usuario_id" in session:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS quantidade
            FROM notificacoes
            WHERE usuario_id = ?
            AND lida = 0
        """, (
            session["usuario_id"],
        ))

        nao_lidas = cursor.fetchone()["quantidade"]
        conexao.close()

    return {
        "csrf_token": gerar_csrf,
        "nao_lidas": nao_lidas
    }


# ==================================================
# PÁGINAS DE ERRO
# ==================================================
@app.errorhandler(400)
def erro_400(erro):
    return render_template(
        "erro.html",
        titulo_erro="Sessão expirada",
        texto_erro=(
            "Não foi possível validar sua solicitação. "
            "Volte à página anterior, atualize e tente novamente."
        )
    ), 400


@app.errorhandler(404)
def erro_404(erro):
    return render_template(
        "erro.html",
        titulo_erro="Página não encontrada",
        texto_erro="O endereço que você tentou acessar não existe."
    ), 404


# ==================================================
# PROTEÇÃO DE ROTAS
# ==================================================
def tutor_required(funcao):
    @wraps(funcao)
    def interna(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("inicio"))
        return funcao(*args, **kwargs)
    return interna


def clinica_required(funcao):
    @wraps(funcao)
    def interna(*args, **kwargs):
        if "clinica_id" not in session:
            return redirect(url_for("clinica_login"))
        return funcao(*args, **kwargs)
    return interna


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================
def inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def criar_notificacao(cursor, usuario_id, titulo, mensagem):
    cursor.execute("""
        INSERT INTO notificacoes (
            usuario_id,
            titulo,
            mensagem
        )
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        titulo,
        mensagem
    ))


def buscar_pet_do_tutor(cursor, pet_id, usuario_id):
    cursor.execute("""
        SELECT *
        FROM pets
        WHERE id = ?
        AND usuario_id = ?
        AND ativo = 1
    """, (
        pet_id,
        usuario_id
    ))
    return cursor.fetchone()


def horario_esta_ocupado(cursor, data, horario):
    cursor.execute("""
        SELECT id
        FROM agendamentos
        WHERE data = ?
        AND horario = ?
        AND status = 'confirmado'
    """, (
        data,
        horario
    ))
    return cursor.fetchone() is not None


def ler_dados_pet():
    """Lê e valida os dados do formulário de pet."""
    nome = request.form.get("nome", "").strip()
    especie = request.form.get("especie", "")
    raca = request.form.get("raca", "").strip()
    idade = inteiro(request.form.get("idade"))

    if not nome or len(nome) > 60:
        return None, "Informe o nome do pet (até 60 caracteres)."

    if especie not in ESPECIES:
        return None, "Selecione uma espécie válida."

    if len(raca) > 60:
        return None, "A raça deve ter até 60 caracteres."

    if idade is None or idade < 0 or idade > 100:
        return None, "Informe uma idade entre 0 e 100 anos."

    return (nome, especie, raca, idade), None


def notificar_lista_espera(cursor, data, horario):
    """
    Quando um horário é liberado, avisa a primeira pessoa
    da lista de espera daquele dia e horário (qualquer serviço).
    """
    cursor.execute("""
        SELECT
            lista_espera.*,
            pets.nome AS pet_nome
        FROM lista_espera
        INNER JOIN pets
        ON lista_espera.pet_id = pets.id
        WHERE lista_espera.data = ?
        AND lista_espera.horario = ?
        AND lista_espera.status = 'aguardando'
        AND pets.ativo = 1
        ORDER BY
            lista_espera.criado_em ASC,
            lista_espera.id ASC
        LIMIT 1
    """, (
        data,
        horario
    ))

    espera = cursor.fetchone()

    if espera is None:
        return

    cursor.execute("""
        UPDATE lista_espera
        SET status = 'notificado'
        WHERE id = ?
    """, (
        espera["id"],
    ))

    criar_notificacao(
        cursor,
        espera["usuario_id"],
        "🔔 Horário disponível!",
        f"O horário de {data_br(data)} às {horario} ficou "
        f"disponível para {espera['pet_nome']} "
        f"({espera['servico']}). Agende agora antes que "
        f"outra pessoa pegue!"
    )


def cancelar_agendamento_db(cursor, agendamento, motivo=""):
    """Cancela, avisa o tutor e avisa a lista de espera."""
    cursor.execute("""
        UPDATE agendamentos
        SET status = 'cancelado'
        WHERE id = ?
        AND status = 'confirmado'
    """, (
        agendamento["id"],
    ))

    criar_notificacao(
        cursor,
        agendamento["usuario_id"],
        "Agendamento cancelado",
        f"O agendamento do dia {data_br(agendamento['data'])} "
        f"às {agendamento['horario']} foi cancelado{motivo}."
    )

    notificar_lista_espera(
        cursor,
        agendamento["data"],
        agendamento["horario"]
    )


# ==================================================
# PÁGINA INICIAL / PERFIL
# ==================================================
@app.route("/")
def inicio():
    if "usuario_id" not in session:
        return render_template(
            "index.html",
            mensagem="Bem-vindo ao PetVida! 🐾"
        )

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE usuario_id = ?
        AND ativo = 1
        ORDER BY nome
    """, (
        session["usuario_id"],
    ))

    pets = cursor.fetchall()

    cursor.execute("""
        SELECT
            agendamentos.*,
            pets.nome AS pet_nome,
            pets.especie AS pet_especie
        FROM agendamentos
        INNER JOIN pets
        ON agendamentos.pet_id = pets.id
        WHERE agendamentos.usuario_id = ?
        AND agendamentos.status = 'confirmado'
        AND agendamentos.data >= ?
        ORDER BY
            agendamentos.data,
            agendamentos.horario
        LIMIT 1
    """, (
        session["usuario_id"],
        date.today().isoformat()
    ))

    proximo = cursor.fetchone()

    conexao.close()

    return render_template(
        "perfil.html",
        nome=session["usuario_nome"],
        pets=pets,
        proximo=proximo
    )


# ==================================================
# CADASTRO
# ==================================================
@app.route("/cadastro", methods=["POST"])
def cadastro():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    if not nome or not email or not senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("inicio"))

    if not EMAIL_REGEX.match(email):
        flash("Informe um email válido.", "erro")
        return redirect(url_for("inicio"))

    if len(senha) < 6:
        flash("A senha precisa ter pelo menos 6 caracteres.", "erro")
        return redirect(url_for("inicio"))

    senha_hash = generate_password_hash(
        senha,
        method="pbkdf2:sha256"
    )

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (
                nome,
                email,
                senha,
                tipo
            )
            VALUES (?, ?, ?, 'tutor')
        """, (
            nome,
            email,
            senha_hash
        ))
        conexao.commit()

    except sqlite3.IntegrityError:
        conexao.close()
        flash("Este email já está cadastrado.", "erro")
        return redirect(url_for("inicio"))

    conexao.close()

    flash("Conta criada com sucesso! Faça login para continuar.", "sucesso")
    return redirect(url_for("inicio"))


# ==================================================
# LOGIN DO TUTOR
# ==================================================
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE email = ?
    """, (
        email,
    ))

    usuario = cursor.fetchone()
    conexao.close()

    if usuario is None or not check_password_hash(
        usuario["senha"],
        senha
    ):
        flash("Email ou senha incorretos.", "erro")
        return redirect(url_for("inicio"))

    session.clear()
    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["tipo"] = "tutor"

    return redirect(url_for("inicio"))


# ==================================================
# LOGOUT
# ==================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


# ==================================================
# ADICIONAR PET
# ==================================================
@app.route("/adicionar_pet")
@tutor_required
def adicionar_pet():
    return render_template(
        "adicionar_pet.html",
        especies=ESPECIES
    )


@app.route("/salvar_pet", methods=["POST"])
@tutor_required
def salvar_pet():
    dados, erro = ler_dados_pet()

    if erro:
        flash(erro, "erro")
        return redirect(url_for("adicionar_pet"))

    nome, especie, raca, idade = dados

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO pets (
            usuario_id,
            nome,
            especie,
            raca,
            idade,
            ativo
        )
        VALUES (?, ?, ?, ?, ?, 1)
    """, (
        session["usuario_id"],
        nome,
        especie,
        raca,
        idade
    ))

    conexao.commit()
    conexao.close()

    flash(f"{nome} foi cadastrado com sucesso! 🐾", "sucesso")
    return redirect(url_for("inicio"))


# ==================================================
# EDITAR PET
# ==================================================
@app.route("/editar_pet/<int:pet_id>")
@tutor_required
def editar_pet(pet_id):
    conexao = conectar()
    cursor = conexao.cursor()

    pet = buscar_pet_do_tutor(
        cursor,
        pet_id,
        session["usuario_id"]
    )

    conexao.close()

    if pet is None:
        flash("Pet não encontrado.", "erro")
        return redirect(url_for("inicio"))

    return render_template(
        "editar_pet.html",
        pet=pet,
        especies=ESPECIES
    )


@app.route(
    "/atualizar_pet/<int:pet_id>",
    methods=["POST"]
)
@tutor_required
def atualizar_pet(pet_id):
    dados, erro = ler_dados_pet()

    if erro:
        flash(erro, "erro")
        return redirect(url_for("editar_pet", pet_id=pet_id))

    nome, especie, raca, idade = dados

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE pets
        SET
            nome = ?,
            especie = ?,
            raca = ?,
            idade = ?
        WHERE id = ?
        AND usuario_id = ?
        AND ativo = 1
    """, (
        nome,
        especie,
        raca,
        idade,
        pet_id,
        session["usuario_id"]
    ))

    conexao.commit()
    conexao.close()

    flash("Dados do pet atualizados.", "sucesso")
    return redirect(url_for("inicio"))


# ==================================================
# REMOVER PET
# ==================================================
@app.route(
    "/remover_pet/<int:pet_id>",
    methods=["POST"]
)
@tutor_required
def remover_pet(pet_id):
    conexao = conectar()
    cursor = conexao.cursor()

    pet = buscar_pet_do_tutor(
        cursor,
        pet_id,
        session["usuario_id"]
    )

    if pet is None:
        conexao.close()
        flash("Pet não encontrado.", "erro")
        return redirect(url_for("inicio"))

    cursor.execute("""
        UPDATE pets
        SET ativo = 0
        WHERE id = ?
    """, (
        pet_id,
    ))

    # Cancela os agendamentos confirmados do pet removido
    # (liberando o horário para a lista de espera).
    cursor.execute("""
        SELECT *
        FROM agendamentos
        WHERE pet_id = ?
        AND status = 'confirmado'
    """, (
        pet_id,
    ))

    for agendamento in cursor.fetchall():
        cancelar_agendamento_db(
            cursor,
            agendamento,
            " porque o pet foi removido"
        )

    cursor.execute("""
        DELETE FROM lista_espera
        WHERE pet_id = ?
        AND status = 'aguardando'
    """, (
        pet_id,
    ))

    conexao.commit()
    conexao.close()

    flash(f"{pet['nome']} foi removido.", "sucesso")
    return redirect(url_for("inicio"))


# ==================================================
# AGENDAMENTO
# ==================================================
@app.route("/agendar")
@tutor_required
def agendar():
    data = request.args.get("data", "").strip()

    if data and not data_valida(data):
        flash("Escolha uma data válida a partir de hoje.", "aviso")
        data = ""

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE usuario_id = ?
        AND ativo = 1
        ORDER BY nome
    """, (
        session["usuario_id"],
    ))

    pets = cursor.fetchall()

    ocupados = []
    passados = []

    if data:
        cursor.execute("""
            SELECT horario
            FROM agendamentos
            WHERE data = ?
            AND status = 'confirmado'
        """, (
            data,
        ))

        ocupados = [
            linha["horario"]
            for linha in cursor.fetchall()
        ]

        passados = horarios_passados(data, HORARIOS)

    conexao.close()

    livres = horarios_disponiveis(
        HORARIOS,
        ocupados + passados
    )

    return render_template(
        "agendar.html",
        pets=pets,
        data=data,
        hoje=date.today().isoformat(),
        horarios=HORARIOS,
        ocupados=ocupados,
        passados=passados,
        livres=livres,
        servicos=SERVICOS
    )


# ==================================================
# SALVAR AGENDAMENTO
# ==================================================
@app.route(
    "/salvar_agendamento",
    methods=["POST"]
)
@tutor_required
def salvar_agendamento():
    usuario_id = session["usuario_id"]

    pet_id = inteiro(request.form.get("pet_id"))
    servico = request.form.get("servico", "")
    data = request.form.get("data", "")
    horario = request.form.get("horario", "")

    if (
        not data_valida(data)
        or horario not in HORARIOS
        or servico not in NOMES_SERVICOS
        or pet_id is None
    ):
        flash("Dados do agendamento inválidos.", "erro")
        return redirect(url_for("agendar"))

    if horario in horarios_passados(data, HORARIOS):
        flash("Esse horário já passou. Escolha outro.", "erro")
        return redirect(url_for("agendar", data=data))

    conexao = conectar()
    cursor = conexao.cursor()

    pet = buscar_pet_do_tutor(cursor, pet_id, usuario_id)

    if pet is None:
        conexao.close()
        flash("Pet inválido.", "erro")
        return redirect(url_for("agendar", data=data))

    if horario_esta_ocupado(cursor, data, horario):
        conexao.close()
        flash(
            "Esse horário acabou de ser ocupado. "
            "Escolha outro ou entre na lista de espera.",
            "erro"
        )
        return redirect(url_for("agendar", data=data))

    try:
        cursor.execute("""
            INSERT INTO agendamentos (
                usuario_id,
                pet_id,
                servico,
                data,
                horario,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'confirmado')
        """, (
            usuario_id,
            pet_id,
            servico,
            data,
            horario
        ))
    except sqlite3.IntegrityError:
        conexao.close()
        flash("Esse horário acabou de ser ocupado.", "erro")
        return redirect(url_for("agendar", data=data))

    # Se a pessoa estava na lista de espera desse horário,
    # a espera é marcada como atendida.
    cursor.execute("""
        UPDATE lista_espera
        SET status = 'atendido'
        WHERE usuario_id = ?
        AND data = ?
        AND horario = ?
        AND status IN ('aguardando', 'notificado')
    """, (
        usuario_id,
        data,
        horario
    ))

    criar_notificacao(
        cursor,
        usuario_id,
        "Agendamento confirmado",
        f"Seu agendamento para {pet['nome']} ({servico}) foi "
        f"confirmado para {data_br(data)} às {horario}."
    )

    conexao.commit()
    conexao.close()

    flash("Agendamento confirmado! ✅", "sucesso")
    return redirect(url_for("meus_agendamentos"))


# ==================================================
# MEUS AGENDAMENTOS
# ==================================================
@app.route("/meus_agendamentos")
@tutor_required
def meus_agendamentos():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            agendamentos.id,
            agendamentos.servico,
            agendamentos.data,
            agendamentos.horario,
            agendamentos.status,
            pets.nome AS pet_nome,
            pets.especie AS pet_especie
        FROM agendamentos
        INNER JOIN pets
        ON agendamentos.pet_id = pets.id
        WHERE agendamentos.usuario_id = ?
        ORDER BY
            agendamentos.data,
            agendamentos.horario
    """, (
        session["usuario_id"],
    ))

    agendamentos = cursor.fetchall()
    conexao.close()

    hoje = date.today().isoformat()

    proximos = [
        ag for ag in agendamentos
        if ag["data"] >= hoje and ag["status"] == "confirmado"
    ]

    historico = [
        ag for ag in agendamentos
        if not (ag["data"] >= hoje and ag["status"] == "confirmado")
    ]
    historico.reverse()

    return render_template(
        "agendamentos.html",
        proximos=proximos,
        historico=historico
    )


# ==================================================
# CANCELAR AGENDAMENTO PELO TUTOR
# ==================================================
@app.route(
    "/cancelar_agendamento/<int:agendamento_id>",
    methods=["POST"]
)
@tutor_required
def cancelar_agendamento(agendamento_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM agendamentos
        WHERE id = ?
        AND usuario_id = ?
        AND status = 'confirmado'
    """, (
        agendamento_id,
        session["usuario_id"]
    ))

    agendamento = cursor.fetchone()

    if agendamento is None:
        conexao.close()
        return redirect(url_for("meus_agendamentos"))

    cancelar_agendamento_db(cursor, agendamento)

    conexao.commit()
    conexao.close()

    flash("Agendamento cancelado.", "sucesso")
    return redirect(url_for("meus_agendamentos"))


# ==================================================
# LISTA DE ESPERA
# ==================================================
@app.route("/lista_espera")
@tutor_required
def lista_espera():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            lista_espera.*,
            pets.nome AS pet_nome,
            pets.especie AS pet_especie
        FROM lista_espera
        INNER JOIN pets
        ON lista_espera.pet_id = pets.id
        WHERE lista_espera.usuario_id = ?
        ORDER BY lista_espera.criado_em DESC
    """, (
        session["usuario_id"],
    ))

    espera = cursor.fetchall()
    conexao.close()

    return render_template(
        "lista_espera.html",
        espera=espera
    )


# ==================================================
# ENTRAR NA LISTA DE ESPERA
# ==================================================
@app.route(
    "/entrar_lista_espera",
    methods=["POST"]
)
@tutor_required
def entrar_lista_espera():
    usuario_id = session["usuario_id"]

    pet_id = inteiro(request.form.get("pet_id"))
    servico = request.form.get("servico", "")
    data = request.form.get("data", "")
    horario = request.form.get("horario", "")

    if (
        not data_valida(data)
        or horario not in HORARIOS
        or servico not in NOMES_SERVICOS
        or pet_id is None
    ):
        flash("Dados inválidos para a lista de espera.", "erro")
        return redirect(url_for("agendar"))

    conexao = conectar()
    cursor = conexao.cursor()

    pet = buscar_pet_do_tutor(cursor, pet_id, usuario_id)

    if pet is None:
        conexao.close()
        flash("Pet inválido.", "erro")
        return redirect(url_for("agendar", data=data))

    # Só faz sentido entrar na espera de um horário ocupado.
    if not horario_esta_ocupado(cursor, data, horario):
        conexao.close()
        flash(
            "Esse horário está livre! Faça o agendamento direto.",
            "aviso"
        )
        return redirect(url_for("agendar", data=data))

    cursor.execute("""
        SELECT id
        FROM lista_espera
        WHERE usuario_id = ?
        AND pet_id = ?
        AND servico = ?
        AND data = ?
        AND horario = ?
        AND status = 'aguardando'
    """, (
        usuario_id,
        pet_id,
        servico,
        data,
        horario
    ))

    existente = cursor.fetchone()

    if existente is None:
        cursor.execute("""
            INSERT INTO lista_espera (
                usuario_id,
                pet_id,
                servico,
                data,
                horario
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            usuario_id,
            pet_id,
            servico,
            data,
            horario
        ))
        flash(
            "Você entrou na lista de espera. "
            "Avisaremos se o horário for liberado. 🔔",
            "sucesso"
        )
    else:
        flash("Você já está nessa lista de espera.", "aviso")

    conexao.commit()
    conexao.close()

    return redirect(url_for("lista_espera"))


# ==================================================
# SAIR DA LISTA DE ESPERA
# ==================================================
@app.route(
    "/sair_lista_espera/<int:espera_id>",
    methods=["POST"]
)
@tutor_required
def sair_lista_espera(espera_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        DELETE FROM lista_espera
        WHERE id = ?
        AND usuario_id = ?
    """, (
        espera_id,
        session["usuario_id"]
    ))

    conexao.commit()
    conexao.close()

    flash("Você saiu da lista de espera.", "sucesso")
    return redirect(url_for("lista_espera"))


# ==================================================
# NOTIFICAÇÕES
# ==================================================
@app.route("/notificacoes")
@tutor_required
def notificacoes():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM notificacoes
        WHERE usuario_id = ?
        ORDER BY criado_em DESC, id DESC
    """, (
        session["usuario_id"],
    ))

    lista = cursor.fetchall()

    cursor.execute("""
        UPDATE notificacoes
        SET lida = 1
        WHERE usuario_id = ?
    """, (
        session["usuario_id"],
    ))

    conexao.commit()
    conexao.close()

    return render_template(
        "notificacoes.html",
        notificacoes=lista
    )


# ==================================================
# LOGIN DA CLÍNICA
# ==================================================
@app.route("/clinica/login", methods=["GET", "POST"])
def clinica_login():
    if request.method == "GET":
        return render_template("clinica_login.html")

    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM clinicas
        WHERE email = ?
    """, (
        email,
    ))

    clinica_encontrada = cursor.fetchone()
    conexao.close()

    if clinica_encontrada is None or not check_password_hash(
        clinica_encontrada["senha"],
        senha
    ):
        flash("Email ou senha incorretos.", "erro")
        return redirect(url_for("clinica_login"))

    session.clear()
    session["clinica_id"] = clinica_encontrada["id"]
    session["clinica_nome"] = clinica_encontrada["nome"]
    session["tipo"] = "clinica"

    return redirect(url_for("clinica"))


# ==================================================
# ÁREA DA CLÍNICA
# ==================================================
@app.route("/clinica")
@clinica_required
def clinica():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            agendamentos.id,
            agendamentos.data,
            agendamentos.horario,
            agendamentos.servico,
            agendamentos.status,
            usuarios.nome AS tutor_nome,
            usuarios.email AS tutor_email,
            pets.nome AS pet_nome,
            pets.especie AS pet_especie
        FROM agendamentos
        INNER JOIN usuarios
        ON agendamentos.usuario_id = usuarios.id
        INNER JOIN pets
        ON agendamentos.pet_id = pets.id
        ORDER BY
            agendamentos.data,
            agendamentos.horario
    """)

    agendamentos = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) AS quantidade
        FROM usuarios
        WHERE tipo = 'tutor'
    """)
    total_tutores = cursor.fetchone()["quantidade"]

    cursor.execute("""
        SELECT COUNT(*) AS quantidade
        FROM pets
        WHERE ativo = 1
    """)
    total_pets = cursor.fetchone()["quantidade"]

    cursor.execute("""
        SELECT COUNT(*) AS quantidade
        FROM lista_espera
        WHERE status = 'aguardando'
    """)
    total_espera = cursor.fetchone()["quantidade"]

    cursor.execute("""
        SELECT COUNT(*) AS quantidade
        FROM agendamentos
        WHERE status = 'confirmado'
    """)
    total_confirmados = cursor.fetchone()["quantidade"]

    conexao.close()

    return render_template(
        "clinica.html",
        nome=session["clinica_nome"],
        agendamentos=agendamentos,
        total_tutores=total_tutores,
        total_pets=total_pets,
        total_espera=total_espera,
        total_confirmados=total_confirmados
    )


# ==================================================
# CONCLUIR AGENDAMENTO PELA CLÍNICA
# ==================================================
@app.route(
    "/clinica/concluir_agendamento/<int:agendamento_id>",
    methods=["POST"]
)
@clinica_required
def clinica_concluir_agendamento(agendamento_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM agendamentos
        WHERE id = ?
        AND status = 'confirmado'
    """, (
        agendamento_id,
    ))

    agendamento = cursor.fetchone()

    if agendamento is None:
        conexao.close()
        return redirect(url_for("clinica"))

    cursor.execute("""
        UPDATE agendamentos
        SET status = 'concluido'
        WHERE id = ?
        AND status = 'confirmado'
    """, (
        agendamento_id,
    ))

    criar_notificacao(
        cursor,
        agendamento["usuario_id"],
        "Atendimento concluído",
        f"O atendimento do dia {data_br(agendamento['data'])} "
        f"às {agendamento['horario']} foi concluído pela clínica."
    )

    conexao.commit()
    conexao.close()

    flash("Atendimento concluído.", "sucesso")
    return redirect(url_for("clinica"))


# ==================================================
# CANCELAR AGENDAMENTO PELA CLÍNICA
# ==================================================
@app.route(
    "/clinica/cancelar_agendamento/<int:agendamento_id>",
    methods=["POST"]
)
@clinica_required
def clinica_cancelar_agendamento(agendamento_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM agendamentos
        WHERE id = ?
        AND status = 'confirmado'
    """, (
        agendamento_id,
    ))

    agendamento = cursor.fetchone()

    if agendamento is None:
        conexao.close()
        return redirect(url_for("clinica"))

    cancelar_agendamento_db(
        cursor,
        agendamento,
        " pela clínica"
    )

    conexao.commit()
    conexao.close()

    flash("Agendamento cancelado.", "sucesso")
    return redirect(url_for("clinica"))


# ==================================================
# LOGOUT DA CLÍNICA
# ==================================================
@app.route("/clinica/logout")
def clinica_logout():
    session.clear()
    return redirect(url_for("clinica_login"))


# ==================================================
# INICIAR SERVIDOR
# ==================================================
if __name__ == "__main__":
    # Para desligar o modo debug: PETVIDA_DEBUG=0
    app.run(
        debug=os.environ.get("PETVIDA_DEBUG", "1") == "1"
    )
