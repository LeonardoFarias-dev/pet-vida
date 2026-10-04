    /* =========================================================
   PETVIDA — JAVASCRIPT GLOBAL
   ========================================================= */


/* =========================================================
   1. CONFIRMAÇÃO DE AÇÕES IMPORTANTES
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /*
       Qualquer formulário que tenha:
       data-confirm="mensagem"

       mostrará uma confirmação antes de enviar.
    */

    const formulariosConfirmacao =
        document.querySelectorAll("form[data-confirm]");

    formulariosConfirmacao.forEach(function (formulario) {

        formulario.addEventListener("submit", function (event) {

            const mensagem =
                formulario.getAttribute("data-confirm");

            const confirmou = window.confirm(mensagem);

            if (!confirmou) {
                event.preventDefault();
            }

        });

    });


    /* =====================================================
       2. ANIMAÇÃO DOS ELEMENTOS
       ===================================================== */

    const elementos =
        document.querySelectorAll(
            ".card, .pet-card, .estatistica, form"
        );

    elementos.forEach(function (elemento, indice) {

        /*
           Pequeno atraso para os elementos aparecerem
           suavemente.
        */

        elemento.style.animationDelay =
            `${indice * 0.03}s`;

    });


    /* =====================================================
       3. VALIDAÇÃO BÁSICA DOS FORMULÁRIOS
       ===================================================== */

    const formularios =
        document.querySelectorAll("form");

    formularios.forEach(function (formulario) {

        formulario.addEventListener("submit", function (event) {

            const camposObrigatorios =
                formulario.querySelectorAll(
                    "input[required], select[required], textarea[required]"
                );

            let formularioValido = true;

            camposObrigatorios.forEach(function (campo) {

                if (!campo.value.trim()) {

                    formularioValido = false;

                    campo.focus();

                    campo.style.borderColor =
                        "#d9534f";

                } else {

                    campo.style.borderColor =
                        "";

                }

            });

            if (!formularioValido) {

                event.preventDefault();

                mostrarMensagem(
                    "Preencha todos os campos obrigatórios.",
                    "erro"
                );

            }

        });

    });


    /* =====================================================
       4. LIMPAR ERRO DO CAMPO AO DIGITAR
       ===================================================== */

    const campos =
        document.querySelectorAll(
            "input, select, textarea"
        );

    campos.forEach(function (campo) {

        campo.addEventListener("input", function () {

            if (campo.value.trim()) {

                campo.style.borderColor = "";

            }

        });

    });


    /* =====================================================
       5. FECHAR MENSAGENS AUTOMATICAMENTE
       ===================================================== */

    const alertas =
        document.querySelectorAll(
            ".alerta-sucesso, .alerta-erro, .alerta-aviso"
        );

    alertas.forEach(function (alerta) {

        setTimeout(function () {

            alerta.style.transition =
                "opacity 0.4s ease, transform 0.4s ease";

            alerta.style.opacity = "0";

            alerta.style.transform =
                "translateY(-8px)";

            setTimeout(function () {

                alerta.remove();

            }, 400);

        }, 5000);

    });


    /* =====================================================
       6. EFEITO NOS BOTÕES
       ===================================================== */

    const botoes =
        document.querySelectorAll(
            "button, .btn"
        );

    botoes.forEach(function (botao) {

        botao.addEventListener("click", function () {

            /*
               Evita que o botão fique visualmente
               "preso" depois do clique.
            */

            botao.blur();

        });

    });


    /* =====================================================
       7. DETECTAR LINKS EXTERNOS
       ===================================================== */

    const links =
        document.querySelectorAll("a");

    links.forEach(function (link) {

        if (
            link.hostname &&
            link.hostname !== window.location.hostname
        ) {

            link.target = "_blank";

            link.rel = "noopener noreferrer";

        }

    });


    /* =====================================================
       8. DATA MÍNIMA PARA CAMPOS DE DATA
       ===================================================== */

    const camposData =
        document.querySelectorAll(
            'input[type="date"]'
        );

    const hoje = new Date();

    const ano =
        hoje.getFullYear();

    const mes =
        String(hoje.getMonth() + 1)
            .padStart(2, "0");

    const dia =
        String(hoje.getDate())
            .padStart(2, "0");

    const dataAtual =
        `${ano}-${mes}-${dia}`;

    camposData.forEach(function (campo) {

        /*
           Impede selecionar uma data anterior
           ao dia atual.
        */

        if (!campo.min) {

            campo.min = dataAtual;

        }

    });


    /* =====================================================
       9. MÁSCARA SIMPLES PARA TELEFONE
       ===================================================== */

    const camposTelefone =
        document.querySelectorAll(
            'input[type="tel"]'
        );

    camposTelefone.forEach(function (campo) {

        campo.addEventListener("input", function () {

            let valor =
                campo.value.replace(/\D/g, "");

            if (valor.length > 11) {

                valor =
                    valor.substring(0, 11);

            }

            if (valor.length <= 10) {

                valor =
                    valor.replace(
                        /^(\d{2})(\d)/,
                        "($1) $2"
                    );

                valor =
                    valor.replace(
                        /(\d{4})(\d)/,
                        "$1-$2"
                    );

            } else {

                valor =
                    valor.replace(
                        /^(\d{2})(\d)/,
                        "($1) $2"
                    );

                valor =
                    valor.replace(
                        /(\d{5})(\d)/,
                        "$1-$2"
                    );

            }

            campo.value = valor;

        });

    });


    /* =====================================================
       10. SENHA — MOSTRAR / ESCONDER
       ===================================================== */

    const botoesSenha =
        document.querySelectorAll(
            "[data-toggle-password]"
        );

    botoesSenha.forEach(function (botao) {

        botao.addEventListener("click", function () {

            const seletor =
                botao.getAttribute(
                    "data-toggle-password"
                );

            const campo =
                document.querySelector(seletor);

            if (!campo) {
                return;
            }

            if (campo.type === "password") {

                campo.type = "text";

                botao.textContent =
                    "Ocultar senha";

            } else {

                campo.type = "password";

                botao.textContent =
                    "Mostrar senha";

            }

        });

    });


    /* =====================================================
       11. CONTADOR DE CARACTERES
       ===================================================== */

    const camposContador =
        document.querySelectorAll(
            "textarea[data-maxlength]"
        );

    camposContador.forEach(function (campo) {

        const limite =
            parseInt(
                campo.getAttribute("data-maxlength")
            );

        if (!limite) {
            return;
        }

        const contador =
            document.createElement("small");

        contador.style.display = "block";

        contador.style.textAlign = "right";

        contador.style.color =
            "#68756f";

        contador.style.marginTop = "-10px";

        contador.style.marginBottom = "12px";

        campo.insertAdjacentElement(
            "afterend",
            contador
        );

        function atualizarContador() {

            const quantidade =
                campo.value.length;

            contador.textContent =
                `${quantidade}/${limite} caracteres`;

        }

        campo.addEventListener(
            "input",
            atualizarContador
        );

        atualizarContador();

    });


    /* =====================================================
       12. CONFIRMAÇÃO ESPECÍFICA PARA REMOVER PET
       ===================================================== */

    const botoesRemover =
        document.querySelectorAll(
            '[data-remover-pet]'
        );

    botoesRemover.forEach(function (botao) {

        botao.addEventListener("click", function (event) {

            const nomePet =
                botao.getAttribute(
                    "data-remover-pet"
                );

            const mensagem =
                nomePet
                    ? `Tem certeza que deseja remover ${nomePet}?`
                    : "Tem certeza que deseja remover este pet?";

            const confirmou =
                window.confirm(mensagem);

            if (!confirmou) {

                event.preventDefault();

            }

        });

    });


    /* =====================================================
       13. DESTACAR HORÁRIO SELECIONADO
       ===================================================== */

    const horarios =
        document.querySelectorAll(
            'input[type="radio"][name="horario"]'
        );

    horarios.forEach(function (radio) {

        radio.addEventListener("change", function () {

            horarios.forEach(function (outroRadio) {

                const label =
                    document.querySelector(
                        `label[for="${outroRadio.id}"]`
                    );

                if (label) {

                    label.style.borderColor = "";

                    label.style.background = "";

                }

            });

            const labelSelecionado =
                document.querySelector(
                    `label[for="${radio.id}"]`
                );

            if (labelSelecionado) {

                labelSelecionado.style.borderColor =
                    "#2e7d5b";

                labelSelecionado.style.background =
                    "#e8f5ee";

            }

        });

    });


    /* =====================================================
       14. CONFIRMAÇÃO DE CANCELAMENTO
       ===================================================== */

    const botoesCancelar =
        document.querySelectorAll(
            '[data-cancelar-agendamento]'
        );

    botoesCancelar.forEach(function (botao) {

        botao.addEventListener("click", function (event) {

            const confirmou =
                window.confirm(
                    "Tem certeza que deseja cancelar este agendamento?"
                );

            if (!confirmou) {

                event.preventDefault();

            }

        });

    });


    /* =====================================================
       15. NOTIFICAÇÃO TEMPORÁRIA
       ===================================================== */

    const notificacoes =
        document.querySelectorAll(
            "[data-notificacao]"
        );

    notificacoes.forEach(function (notificacao) {

        setTimeout(function () {

            notificacao.style.opacity = "0";

            notificacao.style.transform =
                "translateY(-10px)";

            notificacao.style.transition =
                "all 0.4s ease";

            setTimeout(function () {

                notificacao.remove();

            }, 400);

        }, 4000);

    });

});


/* =========================================================
   FUNÇÃO GLOBAL DE MENSAGEM
   ========================================================= */

function mostrarMensagem(
    texto,
    tipo = "sucesso"
) {

    const mensagem =
        document.createElement("div");

    mensagem.className =
        `alerta alerta-${tipo}`;

    mensagem.textContent =
        texto;

    mensagem.style.position =
        "fixed";

    mensagem.style.top =
        "20px";

    mensagem.style.right =
        "20px";

    mensagem.style.zIndex =
        "9999";

    mensagem.style.minWidth =
        "280px";

    mensagem.style.maxWidth =
        "420px";

    mensagem.style.boxShadow =
        "0 10px 30px rgba(31, 58, 45, 0.15)";

    mensagem.style.transition =
        "all 0.4s ease";

    document.body.appendChild(
        mensagem
    );

    setTimeout(function () {

        mensagem.style.opacity =
            "0";

        mensagem.style.transform =
            "translateY(-10px)";

        setTimeout(function () {

            mensagem.remove();

        }, 400);

    }, 4000);

}