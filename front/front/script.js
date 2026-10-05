/* =========================================================
   PETVIDA — JAVASCRIPT GLOBAL
   (carregado com "defer" no base.html)
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       1. CONFIRMAÇÃO DE AÇÕES IMPORTANTES
       Qualquer formulário com data-confirm="mensagem"
       pede confirmação antes de ser enviado.
       ===================================================== */
    document
        .querySelectorAll("form[data-confirm]")
        .forEach(function (formulario) {
            formulario.addEventListener("submit", function (event) {
                const mensagem =
                    formulario.getAttribute("data-confirm");

                if (!window.confirm(mensagem)) {
                    event.preventDefault();
                }
            });
        });


    /* =====================================================
       2. ANIMAÇÃO ESCALONADA DOS CARTÕES
       ===================================================== */
    document
        .querySelectorAll(
            ".card, .pet-card, .estatistica, .form-card, .agendamento, .notificacao"
        )
        .forEach(function (elemento, indice) {
            elemento.style.animationDelay =
                Math.min(indice * 0.04, 0.4) + "s";
        });


    /* =====================================================
       3. VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
       (complementa a validação nativa do navegador)
       ===================================================== */
    document.querySelectorAll("form").forEach(function (formulario) {
        formulario.addEventListener("submit", function (event) {
            const obrigatorios = formulario.querySelectorAll(
                "input[required]:not([type='radio']):not([type='hidden']), " +
                "select[required], textarea[required]"
            );

            let valido = true;
            let primeiroInvalido = null;

            obrigatorios.forEach(function (campo) {
                if (!campo.value.trim()) {
                    valido = false;
                    campo.classList.add("invalido");

                    if (!primeiroInvalido) {
                        primeiroInvalido = campo;
                    }
                } else {
                    campo.classList.remove("invalido");
                }
            });

            if (!valido) {
                event.preventDefault();
                primeiroInvalido.focus();

                mostrarMensagem(
                    "Preencha todos os campos obrigatórios.",
                    "erro"
                );
            }
        });
    });


    /* =====================================================
       4. LIMPAR O ERRO DO CAMPO AO DIGITAR
       ===================================================== */
    document
        .querySelectorAll("input, select, textarea")
        .forEach(function (campo) {
            const limpar = function () {
                if (campo.value.trim()) {
                    campo.classList.remove("invalido");
                }
            };

            campo.addEventListener("input", limpar);
            campo.addEventListener("change", limpar);
        });


    /* =====================================================
       5. FECHAR MENSAGENS AUTOMATICAMENTE
       ===================================================== */
    document
        .querySelectorAll(".mensagens .alerta")
        .forEach(function (alerta) {
            setTimeout(function () {
                esconderElemento(alerta);
            }, 5000);
        });


    /* =====================================================
       6. LINKS EXTERNOS ABREM EM NOVA ABA
       ===================================================== */
    document.querySelectorAll("a[href]").forEach(function (link) {
        if (
            link.hostname &&
            link.hostname !== window.location.hostname
        ) {
            link.target = "_blank";
            link.rel = "noopener noreferrer";
        }
    });


    /* =====================================================
       7. DATA MÍNIMA = HOJE (campos de data)
       ===================================================== */
    const hoje = new Date();
    const dataAtual =
        hoje.getFullYear() + "-" +
        String(hoje.getMonth() + 1).padStart(2, "0") + "-" +
        String(hoje.getDate()).padStart(2, "0");

    document
        .querySelectorAll('input[type="date"]')
        .forEach(function (campo) {
            if (!campo.min) {
                campo.min = dataAtual;
            }
        });


    /* =====================================================
       8. MÁSCARA SIMPLES PARA TELEFONE (input type="tel")
       ===================================================== */
    document
        .querySelectorAll('input[type="tel"]')
        .forEach(function (campo) {
            campo.addEventListener("input", function () {
                let valor = campo.value
                    .replace(/\D/g, "")
                    .substring(0, 11);

                if (valor.length <= 10) {
                    valor = valor
                        .replace(/^(\d{2})(\d)/, "($1) $2")
                        .replace(/(\d{4})(\d)/, "$1-$2");
                } else {
                    valor = valor
                        .replace(/^(\d{2})(\d)/, "($1) $2")
                        .replace(/(\d{5})(\d)/, "$1-$2");
                }

                campo.value = valor;
            });
        });


    /* =====================================================
       9. SENHA — MOSTRAR / OCULTAR
       <button data-toggle-password="#idDoCampo">
       ===================================================== */
    document
        .querySelectorAll("[data-toggle-password]")
        .forEach(function (botao) {
            botao.addEventListener("click", function () {
                const campo = document.querySelector(
                    botao.getAttribute("data-toggle-password")
                );

                if (!campo) {
                    return;
                }

                const mostrando = campo.type === "text";

                campo.type = mostrando ? "password" : "text";
                botao.textContent = mostrando ? "Mostrar" : "Ocultar";
            });
        });


    /* =====================================================
       10. CONTADOR DE CARACTERES
       <textarea data-maxlength="200">
       ===================================================== */
    document
        .querySelectorAll("textarea[data-maxlength]")
        .forEach(function (campo) {
            const limite = parseInt(
                campo.getAttribute("data-maxlength"),
                10
            );

            if (!limite) {
                return;
            }

            const contador = document.createElement("small");
            contador.style.display = "block";
            contador.style.textAlign = "right";
            contador.style.marginTop = "4px";

            campo.setAttribute("maxlength", limite);
            campo.insertAdjacentElement("afterend", contador);

            function atualizar() {
                contador.textContent =
                    campo.value.length + "/" + limite + " caracteres";
            }

            campo.addEventListener("input", atualizar);
            atualizar();
        });


    /* =====================================================
       11. FILTRO DE STATUS NA AGENDA DA CLÍNICA
       ===================================================== */
    const botoesFiltro = document.querySelectorAll(".filtro");

    if (botoesFiltro.length) {
        const linhas = document.querySelectorAll("tbody tr[data-status]");
        const aviso = document.querySelector(".vazio-filtro");

        botoesFiltro.forEach(function (botao) {
            botao.addEventListener("click", function () {
                const filtro = botao.getAttribute("data-filtro");
                let visiveis = 0;

                botoesFiltro.forEach(function (outro) {
                    outro.classList.toggle("ativo", outro === botao);
                });

                linhas.forEach(function (linha) {
                    const mostrar =
                        filtro === "todos" ||
                        linha.getAttribute("data-status") === filtro;

                    linha.hidden = !mostrar;

                    if (mostrar) {
                        visiveis++;
                    }
                });

                if (aviso) {
                    aviso.hidden = visiveis !== 0;
                }
            });
        });
    }
});


/* =========================================================
   FUNÇÕES GLOBAIS
   ========================================================= */

function esconderElemento(elemento) {
    elemento.style.opacity = "0";
    elemento.style.transform = "translateY(-8px)";

    setTimeout(function () {
        elemento.remove();
    }, 400);
}

/*
   Mostra uma mensagem flutuante no canto da tela.
   tipo: "sucesso" | "erro" | "aviso"
*/
function mostrarMensagem(texto, tipo) {
    tipo = tipo || "sucesso";

    const mensagem = document.createElement("div");
    mensagem.className = "alerta alerta-" + tipo + " toast";
    mensagem.setAttribute("role", "status");
    mensagem.textContent = texto;

    document.body.appendChild(mensagem);

    setTimeout(function () {
        esconderElemento(mensagem);
    }, 4000);
}
