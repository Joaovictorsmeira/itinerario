/**
 * Conecta Voluntários — Script Principal
 * Interações: Menu Mobile, Formulário Multi-etapas, Máscara de Telefone,
 * FAQ Acordeão, Modal Acessível e Seleção Rápida de Áreas.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Remove classe de fallback no-js se existir
  document.documentElement.classList.remove("no-js");

  initMobileNav();
  initAreaSelection();
  initMultiStepForm();
  initPhoneMask();
  initMessageCharCounter();
  initFaqAccordion();
  initAlertDismiss();
  initDeleteModal();
});

/* ==========================================================================
   1. MENU MOBILE
   ========================================================================== */
function initMobileNav() {
  const toggleBtn = document.getElementById("nav-toggle");
  const nav = document.getElementById("primary-nav");

  if (!toggleBtn || !nav) return;

  function closeMenu() {
    toggleBtn.setAttribute("aria-expanded", "false");
    nav.classList.remove("is-open");
  }

  toggleBtn.addEventListener("click", () => {
    const isExpanded = toggleBtn.getAttribute("aria-expanded") === "true";
    toggleBtn.setAttribute("aria-expanded", !isExpanded);
    nav.classList.toggle("is-open", !isExpanded);
  });

  nav.querySelectorAll(".nav-link, .btn").forEach(link => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 820) {
        closeMenu();
      }
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && nav.classList.contains("is-open")) {
      closeMenu();
      toggleBtn.focus();
    }
  });
}

/* ==========================================================================
   2. SELEÇÃO DE ÁREA A PARTIR DOS CARDS DE OPORTUNIDADES
   ========================================================================== */
function initAreaSelection() {
  const areaButtons = document.querySelectorAll(".btn-select-area");
  const areaSelect = document.getElementById("select-area");

  areaButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const areaValue = btn.getAttribute("data-area");
      if (areaSelect && areaValue) {
        areaSelect.value = areaValue;

        const formSection = document.getElementById("formulario-inscricao");
        if (formSection) {
          formSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    });
  });
}

/* ==========================================================================
   3. FORMULÁRIO EM ETAPAS (STEP 1 -> STEP 2 -> STEP 3)
   ========================================================================== */
function initMultiStepForm() {
  const form = document.getElementById("volunteer-form");
  if (!form) return;

  const steps = [
    document.getElementById("step-1"),
    document.getElementById("step-2"),
    document.getElementById("step-3"),
  ];
  const stepIndicators = document.querySelectorAll(".step-item");
  let currentStepIndex = 1;

  function showStep(targetStepIndex) {
    steps.forEach((stepEl, idx) => {
      if (!stepEl) return;
      const stepNum = idx + 1;
      if (stepNum === targetStepIndex) {
        stepEl.classList.add("active");
        stepEl.removeAttribute("hidden");
      } else {
        stepEl.classList.remove("active");
        stepEl.setAttribute("hidden", "true");
      }
    });

    stepIndicators.forEach((indicator) => {
      const stepNum = parseInt(indicator.getAttribute("data-step"), 10);
      indicator.classList.remove("active", "completed");
      if (stepNum === targetStepIndex) {
        indicator.classList.add("active");
      } else if (stepNum < targetStepIndex) {
        indicator.classList.add("completed");
      }
    });

    currentStepIndex = targetStepIndex;

    // Se estiver indo para a etapa 3 (Revisão), atualiza os dados do resumo
    if (targetStepIndex === 3) {
      updateReviewSummary();
    }
  }

  // Validação da Etapa 1
  function validateStep1() {
    let isValid = true;
    let firstErrorElement = null;

    const nomeInput = document.getElementById("input-nome");
    const telInput = document.getElementById("input-telefone");
    const emailInput = document.getElementById("input-email");
    const senhaInput = document.getElementById("input-senha");
    const confirmarSenhaInput = document.getElementById("input-confirmar-senha");
    const cidadeInput = document.getElementById("input-cidade");

    clearError(nomeInput, "error-nome");
    clearError(telInput, "error-telefone");
    clearError(emailInput, "error-email");
    clearError(senhaInput, "error-senha");
    clearError(confirmarSenhaInput, "error-confirmar-senha");
    clearError(cidadeInput, "error-cidade");

    // Nome
    if (!nomeInput.value.trim()) {
      showError(nomeInput, "error-nome", "Informe seu nome completo.");
      isValid = false;
      firstErrorElement = firstErrorElement || nomeInput;
    } else if (nomeInput.value.trim().length < 3) {
      showError(nomeInput, "error-nome", "O nome deve ter no mínimo 3 caracteres.");
      isValid = false;
      firstErrorElement = firstErrorElement || nomeInput;
    }

    // Telefone
    const digits = telInput.value.replace(/\D/g, "");
    let national = digits;
    if (digits.startsWith("55") && (digits.length === 12 || digits.length === 13)) {
      national = digits.slice(2);
    }

    if (!digits) {
      showError(telInput, "error-telefone", "O telefone é obrigatório.");
      isValid = false;
      firstErrorElement = firstErrorElement || telInput;
    } else if (national.length !== 10 && national.length !== 11) {
      showError(telInput, "error-telefone", "Informe um telefone válido com DDD (10 ou 11 dígitos).");
      isValid = false;
      firstErrorElement = firstErrorElement || telInput;
    }

    // E-mail (obrigatório para autenticação segura)
    const emailVal = emailInput.value.trim();
    if (!emailVal) {
      showError(emailInput, "error-email", "Informe seu endereço de e-mail.");
      isValid = false;
      firstErrorElement = firstErrorElement || emailInput;
    } else {
      const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
      if (!emailPattern.test(emailVal)) {
        showError(emailInput, "error-email", "Informe um e-mail válido.");
        isValid = false;
        firstErrorElement = firstErrorElement || emailInput;
      }
    }

    // Senha (mínimo 6 caracteres)
    if (!senhaInput.value) {
      showError(senhaInput, "error-senha", "Crie uma senha de acesso.");
      isValid = false;
      firstErrorElement = firstErrorElement || senhaInput;
    } else if (senhaInput.value.length < 6) {
      showError(senhaInput, "error-senha", "A senha deve conter no mínimo 6 caracteres.");
      isValid = false;
      firstErrorElement = firstErrorElement || senhaInput;
    }

    // Confirmação de Senha
    if (!confirmarSenhaInput.value) {
      showError(confirmarSenhaInput, "error-confirmar-senha", "Confirme sua senha.");
      isValid = false;
      firstErrorElement = firstErrorElement || confirmarSenhaInput;
    } else if (confirmarSenhaInput.value !== senhaInput.value) {
      showError(confirmarSenhaInput, "error-confirmar-senha", "As senhas não coincidem.");
      isValid = false;
      firstErrorElement = firstErrorElement || confirmarSenhaInput;
    }

    // Cidade
    if (!cidadeInput.value.trim()) {
      showError(cidadeInput, "error-cidade", "Informe sua cidade ou região.");
      isValid = false;
      firstErrorElement = firstErrorElement || cidadeInput;
    }

    if (firstErrorElement) {
      firstErrorElement.focus();
    }

    return isValid;
  }

  // Validação da Etapa 2
  function validateStep2() {
    let isValid = true;
    let firstErrorElement = null;

    const areaSelect = document.getElementById("select-area");
    const dispSelect = document.getElementById("select-disponibilidade");

    clearError(areaSelect, "error-area");
    clearError(dispSelect, "error-disponibilidade");

    if (!areaSelect.value) {
      showError(areaSelect, "error-area", "Selecione uma área de interesse.");
      isValid = false;
      firstErrorElement = firstErrorElement || areaSelect;
    }

    if (!dispSelect.value) {
      showError(dispSelect, "error-disponibilidade", "Selecione sua disponibilidade de horário.");
      isValid = false;
      firstErrorElement = firstErrorElement || dispSelect;
    }

    if (firstErrorElement) {
      firstErrorElement.focus();
    }

    return isValid;
  }

  // Atualiza o resumo de revisão na Etapa 3
  function updateReviewSummary() {
    const nome = document.getElementById("input-nome").value.trim() || "—";
    const tel = document.getElementById("input-telefone").value.trim() || "—";
    const email = document.getElementById("input-email").value.trim() || "—";
    const cidade = document.getElementById("input-cidade").value.trim() || "—";
    const area = document.getElementById("select-area").value || "—";
    const disp = document.getElementById("select-disponibilidade").value || "—";
    const msg = document.getElementById("textarea-mensagem").value.trim() || "Não informada";

    document.getElementById("review-nome").textContent = nome;
    document.getElementById("review-telefone").textContent = tel;
    document.getElementById("review-email").textContent = email;
    document.getElementById("review-cidade").textContent = cidade;
    document.getElementById("review-area").textContent = area;
    document.getElementById("review-disponibilidade").textContent = disp;
    document.getElementById("review-mensagem").textContent = msg;
  }

  function showError(inputEl, errorId, message) {
    const errSpan = document.getElementById(errorId);
    if (errSpan) errSpan.textContent = message;
    if (inputEl && inputEl.closest(".form-group")) {
      inputEl.closest(".form-group").classList.add("has-error");
    }
  }

  function clearError(inputEl, errorId) {
    const errSpan = document.getElementById(errorId);
    if (errSpan) errSpan.textContent = "";
    if (inputEl && inputEl.closest(".form-group")) {
      inputEl.closest(".form-group").classList.remove("has-error");
    }
  }

  // Event Listeners dos botões "Avançar"
  document.querySelectorAll(".btn-step-next").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetStep = parseInt(btn.getAttribute("data-next-step"), 10);
      if (currentStepIndex === 1 && targetStep === 2) {
        if (validateStep1()) showStep(2);
      } else if (currentStepIndex === 2 && targetStep === 3) {
        if (validateStep2()) showStep(3);
      }
    });
  });

  // Event Listeners dos botões "Voltar"
  document.querySelectorAll(".btn-step-prev").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetStep = parseInt(btn.getAttribute("data-prev-step"), 10);
      showStep(targetStep);
    });
  });

  // Botões de editar direto do resumo
  const editStep1 = document.getElementById("btn-edit-step1");
  const editStep2 = document.getElementById("btn-edit-step2");
  if (editStep1) editStep1.addEventListener("click", () => showStep(1));
  if (editStep2) editStep2.addEventListener("click", () => showStep(2));

  // Validação final e envio
  form.addEventListener("submit", (e) => {
    const checkAuth = document.getElementById("check-autorizacao");
    clearError(checkAuth, "error-autorizacao");

    if (!checkAuth.checked) {
      e.preventDefault();
      showError(checkAuth, "error-autorizacao", "Você deve autorizar o contato para concluir a inscrição.");
      checkAuth.focus();
      return;
    }

    // Desabilita botão de submit para evitar duplo envio
    const submitBtn = document.getElementById("btn-submit");
    if (submitBtn) {
      submitBtn.classList.add("btn-loading");
      submitBtn.setAttribute("disabled", "true");
    }
  });

  // AJUSTE 1: Verifica com textContent.trim() para não considerar espaços vazios como erro
  function hasStepServerErrors(stepId) {
    const stepEl = document.getElementById(stepId);
    if (!stepEl) return false;
    const errorSpans = stepEl.querySelectorAll(".field-error");
    for (const span of errorSpans) {
      if (span.textContent.trim().length > 0) {
        return true;
      }
    }
    return false;
  }

  const serverHasStep1Error = hasStepServerErrors("step-1");
  const serverHasStep2Error = hasStepServerErrors("step-2");
  const serverHasStep3Error = hasStepServerErrors("step-3");

  if (serverHasStep3Error) {
    showStep(3);
  } else if (serverHasStep2Error) {
    showStep(2);
  } else {
    showStep(1);
  }
}

/* ==========================================================================
   4. MÁSCARA DINÂMICA DE TELEFONE
   ========================================================================== */
function initPhoneMask() {
  const telInputs = document.querySelectorAll("input[type='tel'], #input-telefone, #perfil-telefone, #login-telefone");

  telInputs.forEach(telInput => {
    if (!telInput) return;

    telInput.addEventListener("input", (e) => {
      let value = e.target.value.replace(/\D/g, "");

      if (value.startsWith("55") && value.length > 11) {
        value = value.slice(2);
      }

      if (value.length > 11) {
        value = value.slice(0, 11);
      }

      if (value.length > 10) {
        e.target.value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7)}`;
      } else if (value.length > 6) {
        e.target.value = `(${value.slice(0, 2)}) ${value.slice(2, 6)}-${value.slice(6)}`;
      } else if (value.length > 2) {
        e.target.value = `(${value.slice(0, 2)}) ${value.slice(2)}`;
      } else if (value.length > 0) {
        e.target.value = `(${value}`;
      } else {
        e.target.value = "";
      }
    });
  });
}

/* ==========================================================================
   5. CONTADOR DE CARACTERES DA MENSAGEM
   ========================================================================== */
function initMessageCharCounter() {
  const textarea = document.getElementById("textarea-mensagem");
  const counter = document.getElementById("char-counter");
  if (!textarea || !counter) return;

  function update() {
    const len = textarea.value.length;
    counter.textContent = `${len} / 500 caracteres`;
    if (len >= 500) {
      counter.style.color = "var(--color-danger)";
    } else {
      counter.style.color = "var(--color-text-muted)";
    }
  }

  textarea.addEventListener("input", update);
  update();
}

/* ==========================================================================
   6. FAQ ACORDEÃO
   ========================================================================== */
function initFaqAccordion() {
  const faqButtons = document.querySelectorAll(".faq-question");

  faqButtons.forEach(button => {
    button.addEventListener("click", () => {
      const isExpanded = button.getAttribute("aria-expanded") === "true";
      const answer = document.getElementById(button.getAttribute("aria-controls"));
      const faqItem = button.closest(".faq-item");

      faqButtons.forEach(otherBtn => {
        if (otherBtn !== button) {
          otherBtn.setAttribute("aria-expanded", "false");
          const otherAns = document.getElementById(otherBtn.getAttribute("aria-controls"));
          if (otherAns) otherAns.setAttribute("hidden", "true");
          const otherItem = otherBtn.closest(".faq-item");
          if (otherItem) otherItem.classList.remove("is-open");
        }
      });

      button.setAttribute("aria-expanded", !isExpanded);
      if (isExpanded) {
        if (answer) answer.setAttribute("hidden", "true");
        if (faqItem) faqItem.classList.remove("is-open");
      } else {
        if (answer) answer.removeAttribute("hidden");
        if (faqItem) faqItem.classList.add("is-open");
      }
    });
  });
}

/* ==========================================================================
   7. FECHAMENTO DE ALERTAS FLASH
   ========================================================================== */
function initAlertDismiss() {
  document.querySelectorAll(".alert-close").forEach(btn => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 180);
      }
    });
  });
}

/* ==========================================================================
   8. MODAL ACESSÍVEL DE EXCLUSÃO
   ========================================================================== */
function initDeleteModal() {
  const openBtn = document.getElementById("btn-open-delete-modal");
  const modal = document.getElementById("delete-modal");
  const cancelBtn = document.getElementById("btn-cancel-delete");

  if (!openBtn || !modal) return;

  function openModal() {
    modal.removeAttribute("hidden");
    if (cancelBtn) cancelBtn.focus();
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.setAttribute("hidden", "true");
    openBtn.focus();
    document.body.style.overflow = "";
  }

  openBtn.addEventListener("click", openModal);
  if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.hasAttribute("hidden")) {
      closeModal();
    }
  });
}
