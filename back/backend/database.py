import os
import sqlite3
from werkzeug.security import generate_password_hash

# O banco fica sempre na mesma pasta deste arquivo,
# não importa de onde o Flask foi iniciado.
CAMINHO_BANCO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "petvida.db"
)

# Senha da clínica padrão. Em produção, defina a variável
# de ambiente PETVIDA_CLINICA_SENHA antes de rodar pela 1ª vez.
SENHA_CLINICA_PADRAO = os.environ.get(
    "PETVIDA_CLINICA_SENHA",
    "123456"
)


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = cursor.fetchall()
    return any(
        coluna_info[1] == coluna
        for coluna_info in colunas
    )


def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    # ==========================================
    # USUÁRIOS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    if not coluna_existe(cursor, "usuarios", "tipo"):
        cursor.execute("""
            ALTER TABLE usuarios
            ADD COLUMN tipo TEXT NOT NULL DEFAULT 'tutor'
        """)

    # ==========================================
    # PETS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            raca TEXT,
            idade INTEGER,
            FOREIGN KEY (usuario_id)
            REFERENCES usuarios(id)
        )
    """)

    if not coluna_existe(cursor, "pets", "ativo"):
        cursor.execute("""
            ALTER TABLE pets
            ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1
        """)

    # ==========================================
    # AGENDAMENTOS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pet_id INTEGER NOT NULL,
            servico TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmado',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id)
            REFERENCES usuarios(id),
            FOREIGN KEY (pet_id)
            REFERENCES pets(id)
        )
    """)

    # Garante no próprio banco que não existem dois agendamentos
    # confirmados no mesmo dia e horário (evita conflito se duas
    # pessoas agendarem ao mesmo tempo).
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_agendamento_horario_confirmado
            ON agendamentos (data, horario)
            WHERE status = 'confirmado'
        """)
    except sqlite3.IntegrityError:
        # Já existem duplicados antigos no banco; o app continua
        # validando o horário pelo código.
        pass

    # ==========================================
    # LISTA DE ESPERA
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lista_espera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pet_id INTEGER NOT NULL,
            servico TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'aguardando',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id)
            REFERENCES usuarios(id),
            FOREIGN KEY (pet_id)
            REFERENCES pets(id)
        )
    """)

    # ==========================================
    # NOTIFICAÇÕES
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            lida INTEGER NOT NULL DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id)
            REFERENCES usuarios(id)
        )
    """)

    # ==========================================
    # CLÍNICAS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    # Cria a clínica padrão somente se ela ainda não existir.
    cursor.execute("""
        SELECT *
        FROM clinicas
        WHERE email = ?
    """, ("clinica@petvida.com",))

    clinica = cursor.fetchone()

    if clinica is None:
        senha_hash = generate_password_hash(
            SENHA_CLINICA_PADRAO,
            method="pbkdf2:sha256"
        )

        cursor.execute("""
            INSERT INTO clinicas (
                nome,
                email,
                senha
            )
            VALUES (?, ?, ?)
        """, (
            "PetVida Clínica",
            "clinica@petvida.com",
            senha_hash
        ))

    conexao.commit()
    conexao.close()


criar_tabelas()
