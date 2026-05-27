const API_BASE = '';

const RESET_LANG = {
  en: {
    'validate_email':       'Enter a valid email',
    'validate_code':        'Enter a 6-digit numeric code',
    'err_send_failed':      'Send error',
    'err_resend_failed':    'Failed to resend code',
    'err_resend_ok':        'Code resent',
    'err_wrong_code':       'Invalid code',
    'err_generic':          'Error',
    'pwd_changed':          'Password changed! Redirecting...',
    'pwd_mismatch':         'Passwords do not match',
    'btn_request':          'Request code →',
    'btn_resend':           'Resend',
    'btn_resend_countdown': 'Resend ({s}s)',
    'validate_pwd_short':   'Password must be longer than 8 characters',
    'validate_pwd_letter':  'Password must contain at least one letter',
    'validate_pwd_digits':  'Password must contain at least 2 digits',
    'validate_pwd_special': 'Password must contain at least 1 special character',
  },
  ru: {
    'validate_email':       'Введите корректный email',
    'validate_code':        'Введите 6-значный числовой код',
    'err_send_failed':      'Ошибка отправки',
    'err_resend_failed':    'Не удалось выслать код',
    'err_resend_ok':        'Код выслан повторно',
    'err_wrong_code':       'Неверный код',
    'err_generic':          'Ошибка',
    'pwd_changed':          'Пароль изменён! Перенаправление...',
    'pwd_mismatch':         'Пароли не совпадают',
    'btn_request':          'Получить код →',
    'btn_resend':           'Выслать повторно',
    'btn_resend_countdown': 'Выслать повторно ({s}с)',
    'validate_pwd_short':   'Пароль должен быть длиннее 8 символов',
    'validate_pwd_letter':  'Пароль должен содержать хотя бы одну букву',
    'validate_pwd_digits':  'Пароль должен содержать минимум 2 цифры',
    'validate_pwd_special': 'Пароль должен содержать минимум 1 специальный символ',
  },
};

const resetLang = localStorage.getItem('kanbee_lang') || 'ru';

function tR(key) {
  return (RESET_LANG[resetLang] && RESET_LANG[resetLang][key]) || RESET_LANG.ru[key] || key;
}

function tRErr(err) {
  try {
    const detail = JSON.parse(err.message).detail;
    if (typeof detail === 'string') {
      const known = RESET_LANG[resetLang] && RESET_LANG[resetLang][detail];
      return known || detail;
    }
  } catch {}
  return err.message || tR('err_generic');
}

function bindPasswordToggles() {
  const eyeOpen = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
  const eyeOff  = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
  document.querySelectorAll('input[type="password"]').forEach(input => {
    const wrap = document.createElement('div');
    wrap.className = 'pwd-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pwd-toggle-btn';
    btn.innerHTML = eyeOpen;
    wrap.appendChild(btn);
    btn.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.innerHTML = show ? eyeOff : eyeOpen;
    });
  });
}

async function api(method, path, body = null) {
  const opts = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  if (!res.ok) {
    const text = await res.text();
    const err = new Error(text);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

function validatePassword(password) {
  if (password.length <= 8) return tR('validate_pwd_short');
  if (!/[a-zA-Zа-яА-ЯёЁ]/.test(password)) return tR('validate_pwd_letter');
  if ((password.match(/\d/g) || []).length < 2) return tR('validate_pwd_digits');
  if (!/[^a-zA-Zа-яА-ЯёЁ\d]/.test(password)) return tR('validate_pwd_special');
  return null;
}

function showError(el, msg, success = false) {
  el.style.color = success ? 'var(--done)' : '';
  el.textContent = msg;
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await api('GET', '/auth/me');
    window.location.replace('/board');
    return;
  } catch {
    // not logged in
  }

  bindPasswordToggles();

  let resetEmail = '';
  let resendTimer = null;

  const step1 = document.getElementById('step-1');
  const step2 = document.getElementById('step-2');
  const step3 = document.getElementById('step-3');

  const emailEl        = document.getElementById('reset-email');
  const step1Error     = document.getElementById('step1-error');
  const btnRequestCode = document.getElementById('btn-request-code');

  const emailDisplay   = document.getElementById('reset-email-display');
  const codeEl         = document.getElementById('reset-code');
  const step2Error     = document.getElementById('step2-error');
  const btnVerifyCode  = document.getElementById('btn-verify-code');
  const btnResendCode  = document.getElementById('btn-resend-code');

  const newPassEl       = document.getElementById('reset-new-password');
  const confirmPassEl   = document.getElementById('reset-confirm-password');
  const step3Error      = document.getElementById('step3-error');
  const btnConfirmReset = document.getElementById('btn-confirm-reset');

  function showStep(n) {
    step1.style.display = n === 1 ? '' : 'none';
    step2.style.display = n === 2 ? '' : 'none';
    step3.style.display = n === 3 ? '' : 'none';
  }

  // ── Step 1: request code ─────────────────────────────────────────

  async function requestCode() {
    step1Error.textContent = '';
    const email = emailEl.value.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError(step1Error, tR('validate_email')); return;
    }
    btnRequestCode.disabled = true;
    try {
      await api('POST', '/auth/request-reset', { email });
      resetEmail = email;
      emailDisplay.textContent = email;
      codeEl.value = '';
      step2Error.textContent = '';
      showStep(2);
    } catch (err) {
      showError(step1Error, tRErr(err));
      if (err.status === 429) {
        btnRequestCode.disabled = true;
        let secs = 120;
        const timer = setInterval(() => {
          secs--;
          btnRequestCode.textContent = tR('btn_resend_countdown').replace('{s}', secs);
          if (secs <= 0) { clearInterval(timer); btnRequestCode.disabled = false; btnRequestCode.textContent = tR('btn_request'); }
        }, 1000);
      } else {
        btnRequestCode.disabled = false;
      }
    }
  }

  btnRequestCode.addEventListener('click', requestCode);
  emailEl.addEventListener('keydown', e => { if (e.key === 'Enter') requestCode(); });

  // ── Step 2: verify code ──────────────────────────────────────────

  btnResendCode.addEventListener('click', async () => {
    if (resendTimer) return;
    step2Error.textContent = '';
    btnResendCode.disabled = true;
    try {
      await api('POST', '/auth/request-reset', { email: resetEmail });
      showError(step2Error, tR('err_resend_ok'), true);
      codeEl.value = '';
    } catch {
      showError(step2Error, tR('err_resend_failed'));
    }
    // cooldown 2 minutes
    let secs = 120;
    btnResendCode.textContent = tR('btn_resend_countdown').replace('{s}', secs);
    resendTimer = setInterval(() => {
      secs--;
      if (secs <= 0) {
        clearInterval(resendTimer);
        resendTimer = null;
        btnResendCode.disabled = false;
        btnResendCode.textContent = tR('btn_resend');
      } else {
        btnResendCode.textContent = tR('btn_resend_countdown').replace('{s}', secs);
      }
    }, 1000);
  });

  function isAttemptsExceeded(msg) {
    return msg && (msg.includes('err_code_attempts_exceeded') || msg.includes('Превышено'));
  }

  async function verifyCode() {
    step2Error.style.color = '';
    step2Error.textContent = '';
    const code = codeEl.value.trim();
    if (!/^\d{6}$/.test(code)) {
      showError(step2Error, tR('validate_code')); return;
    }
    btnVerifyCode.disabled = true;
    try {
      await api('POST', '/auth/verify-reset', { email: resetEmail, code });
      newPassEl.value = '';
      confirmPassEl.value = '';
      step3Error.textContent = '';
      showStep(3);
    } catch (err) {
      const msg = tRErr(err);
      showError(step2Error, msg);
      if (!isAttemptsExceeded(msg)) {
        btnVerifyCode.disabled = false;
      }
    }
  }

  btnVerifyCode.addEventListener('click', verifyCode);
  codeEl.addEventListener('keydown', e => { if (e.key === 'Enter') verifyCode(); });

  // only allow digits in code field
  codeEl.addEventListener('input', () => {
    codeEl.value = codeEl.value.replace(/\D/g, '').slice(0, 6);
  });

  // ── Step 3: confirm new password ─────────────────────────────────

  btnConfirmReset.addEventListener('click', async () => {
    step3Error.style.color = '';
    step3Error.textContent = '';
    const password = newPassEl.value;
    const confirm  = confirmPassEl.value;
    const pwErr = validatePassword(password);
    if (pwErr) { showError(step3Error, pwErr); return; }
    if (password !== confirm) { showError(step3Error, tR('pwd_mismatch')); return; }

    btnConfirmReset.disabled = true;
    try {
      const code = codeEl.value.trim();
      await api('POST', '/auth/confirm-reset', {
        email: resetEmail,
        code,
        new_password: password,
      });
      showError(step3Error, tR('pwd_changed'), true);
      setTimeout(() => window.location.replace('/registration'), 1500);
    } catch (err) {
      showError(step3Error, tRErr(err));
      btnConfirmReset.disabled = false;
    }
  });
});
