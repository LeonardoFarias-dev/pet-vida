# 🐾 PetVida

## Sistema de gestão para clínica veterinária

O **PetVida** é um sistema web desenvolvido para auxiliar na organização de agendamentos e no gerenciamento de atendimentos de uma clínica veterinária.

## 🎯 Problema

Clínicas veterinárias podem enfrentar problemas relacionados a:

* excesso de agendamentos;
* cancelamentos;
* faltas;
* horários que ficam disponíveis novamente;
* dificuldade para organizar a fila de espera.

## 💡 Solução

O PetVida busca centralizar o gerenciamento dos atendimentos, facilitando a organização da agenda e o acompanhamento dos tutores e seus pets.

### Para os tutores

O sistema permite que os tutores:

* criem uma conta;
* façam login;
* cadastrem seus pets;
* agendem atendimentos;
* acompanhem seus agendamentos;
* recebam notificações;
* utilizem a lista de espera quando necessário.

### Para a clínica

A clínica pode:

* visualizar os agendamentos;
* acompanhar tutores e pets;
* gerenciar atendimentos;
* controlar a agenda;
* gerenciar cancelamentos;
* trabalhar com lista de espera.

## 🛠️ Tecnologias

* HTML
* CSS
* JavaScript
* Python
* Flask
* SQLite
* Git
* GitHub

## 📁 Estrutura do projeto

```text
petvida-clinica/
├── back/
│   ├── app.py
│   ├── database.py
│   └── templates/
│
├── front/
│   ├── style.css
│   └── script.js
│
├── .gitignore
├── LICENSE
└── README.md
```

## 🚧 Status

**Projeto em desenvolvimento.**

O sistema possui funcionalidades de cadastro, login, gerenciamento de pets, agendamentos, notificações, lista de espera e área da clínica.

## ▶️ Como executar

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/LeonardoFarias-Dev/pet-vida.git
cd pet-vida
```

Entre na pasta do backend:

```bash
cd back
```

Instale o Flask:

```bash
python3 -m pip install flask
```

Execute o sistema:

```bash
python3 app.py
```

Depois, acesse no navegador:

```text
http://127.0.0.1:5000
```

## 📄 Licença

Este projeto está licenciado sob a licença **MIT**.
