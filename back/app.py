import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect
)

from database import conectar

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ==================================================
# CONFIGURAÇÃO DO FLASK
# ==================================================

app = Flask(
    __name__,
    static_folder="../front",
    static_url_path="/static"
)

app.secret_key = "petvida-chave-secreta"

app.config["SESSION_PERMANENT"] = False


# ==================================================
# HORÁRIOS
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
    "17:00"
]


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
        SELECT COUNT(*) AS quantidade
        FROM notificacoes
        WHERE usuario_id = ?
        AND lida = 0
    """, (
        session["usuario_id"],
    ))

    notificacoes_nao_lidas = cursor.fetchone()["quantidade"]

    conexao.close()

    return render_template(
        "perfil.html",
        nome=session["usuario_nome"],
        pets=pets,
        notificacoes_nao_lidas=notificacoes_nao_lidas
    )


# ==================================================
# CADASTRO
# ==================================================

@app.route("/cadastro", methods=["POST"])
def cadastro():

    nome = request.form["nome"].strip()
    email = request.form["email"].strip().lower()
    senha = request.form["senha"]

    if not nome or not email or not senha:

        return """
        <h1>❌ Preencha todos os campos.</h1>
        <a href="/">Voltar</a>
        """

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

        return """
        <h1>❌ Email já cadastrado.</h1>
        <a href="/">Voltar</a>
        """

    conexao.close()

    return """
    <h1>✅ Cadastro realizado!</h1>

    <p>
        Sua conta foi criada com sucesso.
    </p>

    <a href="/">
        Voltar para o login
    </a>
    """


# ==================================================
# LOGIN DO TUTOR
# ==================================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"].strip().lower()
    senha = request.form["senha"]

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

    if usuario is None:

        return """
        <h1>❌ Login inválido.</h1>

        <p>
            Email ou senha incorretos.
        </p>

        <a href="/">
            Voltar
        </a>
        """

    if not check_password_hash(
        usuario["senha"],
        senha
    ):

        return """
        <h1>❌ Login inválido.</h1>

        <p>
            Email ou senha incorretos.
        </p>

        <a href="/">
            Voltar
        </a>
        """

    session.clear()

    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["tipo"] = "tutor"

    return redirect("/")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==================================================
# ADICIONAR PET
# ==================================================

@app.route("/adicionar_pet")
def formulario_pet():

    if "usuario_id" not in session:

        return redirect("/")

    return render_template(
        "adicionar_pet.html"
    )


@app.route("/salvar_pet", methods=["POST"])
def salvar_pet():

    if "usuario_id" not in session:

        return redirect("/")

    nome = request.form["nome"].strip()
    especie = request.form["especie"]
    raca = request.form["raca"].strip()
    idade = request.form["idade"]

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

    return redirect("/")


# ==================================================
# EDITAR PET
# ==================================================

@app.route("/editar_pet/<int:pet_id>")
def editar_pet(pet_id):

    if "usuario_id" not in session:

        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE id = ?
        AND usuario_id = ?
        AND ativo = 1
    """, (
        pet_id,
        session["usuario_id"]
    ))

    pet = cursor.fetchone()

    conexao.close()

    if pet is None:

        return """
        <h1>❌ Pet não encontrado.</h1>

        <a href="/">
            Voltar
        </a>
        """

    return render_template(
        "editar_pet.html",
        pet=pet
    )


@app.route(
    "/atualizar_pet/<int:pet_id>",
    methods=["POST"]
)
def atualizar_pet(pet_id):

    if "usuario_id" not in session:

        return redirect("/")

    nome = request.form["nome"].strip()
    especie = request.form["especie"]
    raca = request.form["raca"].strip()
    idade = request.form["idade"]

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

    return redirect("/")


# ==================================================
# REMOVER PET
# ==================================================

@app.route(
    "/remover_pet/<int:pet_id>",
    methods=["POST"]
)
def remover_pet(pet_id):

    if "usuario_id" not in session:

        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE pets
        SET ativo = 0
        WHERE id = ?
        AND usuario_id = ?
        AND ativo = 1
    """, (
        pet_id,
        session["usuario_id"]
    ))

    conexao.commit()
    conexao.close()

    return redirect("/")


# ==================================================
# AGENDAMENTO
# ==================================================

@app.route("/agendar")
def agendar():

    if "usuario_id" not in session:

        return redirect("/")

    data = request.args.get("data", "")

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

    conexao.close()

    return render_template(
        "agendar.html",
        pets=pets,
        data=data,
        horarios=HORARIOS,
        ocupados=ocupados
    )


# ==================================================
# SALVAR AGENDAMENTO
# ==================================================

@app.route(
    "/salvar_agendamento",
    methods=["POST"]
)
def salvar_agendamento():

    if "usuario_id" not in session:

        return redirect("/")

    usuario_id = session["usuario_id"]

    pet_id = request.form["pet_id"]
    servico = request.form["servico"]
    data = request.form["data"]
    horario = request.form["horario"]

    conexao = conectar()
    cursor = conexao.cursor()

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

    pet = cursor.fetchone()

    if pet is None:

        conexao.close()

        return """
        <h1>❌ Pet inválido.</h1>

        <a href="/agendar">
            Voltar
        </a>
        """

    cursor.execute("""
        SELECT *
        FROM agendamentos
        WHERE data = ?
        AND horario = ?
        AND status = 'confirmado'
    """, (
        data,
        horario
    ))

    ocupado = cursor.fetchone()

    if ocupado is not None:

        conexao.close()

        return """
        <h1>❌ Horário ocupado.</h1>

        <p>
            Escolha outro horário.
        </p>

        <a href="/agendar">
            Voltar
        </a>
        """

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

    cursor.execute("""
        INSERT INTO notificacoes (
            usuario_id,
            titulo,
            mensagem
        )
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        "Agendamento confirmado",
        f"Seu agendamento para {pet['nome']} foi confirmado para {data} às {horario}."
    ))

    conexao.commit()
    conexao.close()

    return redirect("/meus_agendamentos")


# ==================================================
# MEUS AGENDAMENTOS
# ==================================================

@app.route("/meus_agendamentos")
def meus_agendamentos():

    if "usuario_id" not in session:

        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT

            agendamentos.id,

            agendamentos.servico,

            agendamentos.data,

            agendamentos.horario,

            agendamentos.status,

            pets.nome AS pet_nome

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

    return render_template(
        "agendamentos.html",
        agendamentos=agendamentos
    )


# ==================================================
# CANCELAR AGENDAMENTO PELO TUTOR
# ==================================================

@app.route(
    "/cancelar_agendamento/<int:agendamento_id>",
    methods=["POST"]
)
def cancelar_agendamento(agendamento_id):

    if "usuario_id" not in session:

        return redirect("/")

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

        return redirect("/meus_agendamentos")

    cursor.execute("""
        UPDATE agendamentos
        SET status = 'cancelado'
        WHERE id = ?
        AND usuario_id = ?
    """, (
        agendamento_id,
        session["usuario_id"]
    ))

    cursor.execute("""
        INSERT INTO notificacoes (
            usuario_id,
            titulo,
            mensagem
        )
        VALUES (?, ?, ?)
    """, (
        session["usuario_id"],
        "Agendamento cancelado",
        f"O agendamento do dia {agendamento['data']} às {agendamento['horario']} foi cancelado."
    ))

    cursor.execute("""
        SELECT *
        FROM lista_espera
        WHERE data = ?
        AND horario = ?
        AND servico = ?
        AND status = 'aguardando'
        ORDER BY criado_em ASC
        LIMIT 1
    """, (
        agendamento["data"],
        agendamento["horario"],
        agendamento["servico"]
    ))

    espera = cursor.fetchone()

    if espera is not None:

        cursor.execute("""
            UPDATE lista_espera
            SET status = 'notificado'
            WHERE id = ?
        """, (
            espera["id"],
        ))

        cursor.execute("""
            INSERT INTO notificacoes (
                usuario_id,
                titulo,
                mensagem
            )
            VALUES (?, ?, ?)
        """, (
            espera["usuario_id"],
            "🔔 Horário disponível!",
            f"Um horário de {agendamento['servico']} ficou disponível para {agendamento['data']} às {agendamento['horario']}."
        ))

    conexao.commit()
    conexao.close()

    return redirect("/meus_agendamentos")


# ==================================================
# LISTA DE ESPERA
# ==================================================

@app.route("/lista_espera")
def lista_espera():

    if "usuario_id" not in session:

        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT

            lista_espera.*,

            pets.nome AS pet_nome

        FROM lista_espera

        INNER JOIN pets
        ON lista_espera.pet_id = pets.id

        WHERE lista_espera.usuario_id = ?

        ORDER BY criado_em DESC
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
def entrar_lista_espera():

    if "usuario_id" not in session:

        return redirect("/")

    usuario_id = session["usuario_id"]

    pet_id = request.form["pet_id"]
    servico = request.form["servico"]
    data = request.form["data"]
    horario = request.form["horario"]

    conexao = conectar()
    cursor = conexao.cursor()

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

    pet = cursor.fetchone()

    if pet is None:

        conexao.close()

        return redirect("/")

    cursor.execute("""
        SELECT *
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

    conexao.commit()
    conexao.close()

    return redirect("/lista_espera")


# ==================================================
# SAIR DA LISTA DE ESPERA
# ==================================================

@app.route(
    "/sair_lista_espera/<int:espera_id>",
    methods=["POST"]
)
def sair_lista_espera(espera_id):

    if "usuario_id" not in session:

        return redirect("/")

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

    return redirect("/lista_espera")


# ==================================================
# NOTIFICAÇÕES
# ==================================================

@app.route("/notificacoes")
def notificacoes():

    if "usuario_id" not in session:

        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM notificacoes
        WHERE usuario_id = ?
        ORDER BY criado_em DESC
    """, (
        session["usuario_id"],
    ))

    notificacoes = cursor.fetchall()

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
        notificacoes=notificacoes
    )


# ==================================================
# LOGIN DA CLÍNICA
# ==================================================

@app.route("/clinica/login")
def clinica_login():

    return render_template(
        "clinica_login.html"
    )


@app.route(
    "/clinica/login",
    methods=["POST"]
)
def clinica_login_post():

    email = request.form["email"].strip().lower()
    senha = request.form["senha"]

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM clinicas
        WHERE email = ?
    """, (
        email,
    ))

    clinica = cursor.fetchone()

    conexao.close()

    if clinica is None:

        return """
        <h1>❌ Login inválido.</h1>

        <a href="/clinica/login">
            Voltar
        </a>
        """

    if not check_password_hash(
        clinica["senha"],
        senha
    ):

        return """
        <h1>❌ Login inválido.</h1>

        <a href="/clinica/login">
            Voltar
        </a>
        """

    session.clear()

    session["clinica_id"] = clinica["id"]
    session["clinica_nome"] = clinica["nome"]
    session["tipo"] = "clinica"

    return redirect("/clinica")


# ==================================================
# ÁREA DA CLÍNICA
# ==================================================

@app.route("/clinica")
def clinica():

    if "clinica_id" not in session:

        return redirect("/clinica/login")

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

            pets.nome AS pet_nome

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

    conexao.close()

    return render_template(
        "clinica.html",
        nome=session["clinica_nome"],
        agendamentos=agendamentos,
        total_tutores=total_tutores,
        total_pets=total_pets,
        total_espera=total_espera
    )


# ==================================================
# CONCLUIR AGENDAMENTO PELA CLÍNICA
# ==================================================

@app.route(
    "/clinica/concluir_agendamento/<int:agendamento_id>",
    methods=["POST"]
)
def clinica_concluir_agendamento(agendamento_id):

    if "clinica_id" not in session:

        return redirect("/clinica/login")

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

        return redirect("/clinica")

    cursor.execute("""
        UPDATE agendamentos
        SET status = 'concluido'
        WHERE id = ?
        AND status = 'confirmado'
    """, (
        agendamento_id,
    ))

    cursor.execute("""
        INSERT INTO notificacoes (
            usuario_id,
            titulo,
            mensagem
        )
        VALUES (?, ?, ?)
    """, (
        agendamento["usuario_id"],
        "Atendimento concluído",
        f"O atendimento do dia {agendamento['data']} às {agendamento['horario']} foi concluído pela clínica."
    ))

    conexao.commit()
    conexao.close()

    return redirect("/clinica")


# ==================================================
# CANCELAR AGENDAMENTO PELA CLÍNICA
# ==================================================

@app.route(
    "/clinica/cancelar_agendamento/<int:agendamento_id>",
    methods=["POST"]
)
def clinica_cancelar_agendamento(agendamento_id):

    if "clinica_id" not in session:

        return redirect("/clinica/login")

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

        return redirect("/clinica")

    cursor.execute("""
        UPDATE agendamentos
        SET status = 'cancelado'
        WHERE id = ?
        AND status = 'confirmado'
    """, (
        agendamento_id,
    ))

    cursor.execute("""
        INSERT INTO notificacoes (
            usuario_id,
            titulo,
            mensagem
        )
        VALUES (?, ?, ?)
    """, (
        agendamento["usuario_id"],
        "Agendamento cancelado",
        f"O agendamento do dia {agendamento['data']} às {agendamento['horario']} foi cancelado pela clínica."
    ))

    cursor.execute("""
        SELECT *
        FROM lista_espera
        WHERE data = ?
        AND horario = ?
        AND servico = ?
        AND status = 'aguardando'
        ORDER BY criado_em ASC
        LIMIT 1
    """, (
        agendamento["data"],
        agendamento["horario"],
        agendamento["servico"]
    ))

    espera = cursor.fetchone()

    if espera is not None:

        cursor.execute("""
            UPDATE lista_espera
            SET status = 'notificado'
            WHERE id = ?
        """, (
            espera["id"],
        ))

        cursor.execute("""
            INSERT INTO notificacoes (
                usuario_id,
                titulo,
                mensagem
            )
            VALUES (?, ?, ?)
        """, (
            espera["usuario_id"],
            "🔔 Horário disponível!",
            f"Um horário de {agendamento['servico']} ficou disponível para {agendamento['data']} às {agendamento['horario']}."
        ))

    conexao.commit()
    conexao.close()

    return redirect("/clinica")


# ==================================================
# LOGOUT DA CLÍNICA
# ==================================================

@app.route("/clinica/logout")
def clinica_logout():

    session.clear()

    return redirect("/clinica/login")


# ==================================================
# INICIAR SERVIDOR
# ==================================================

if __name__ == "__main__":

    app.run(debug=True)