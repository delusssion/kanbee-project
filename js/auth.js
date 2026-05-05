const API_BASE = '';

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

function validateEmail(email) {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Введите корректный email';
  return null;
}

function validatePassword(password) {
  if (password.length <= 8) return 'Пароль должен быть длиннее 8 символов';
  if (!/[a-zA-Zа-яА-ЯёЁ]/.test(password)) return 'Пароль должен содержать хотя бы одну букву';
  if ((password.match(/\d/g) || []).length < 2) return 'Пароль должен содержать минимум 2 цифры';
  if (!/[^a-zA-Zа-яА-ЯёЁ\d]/.test(password)) return 'Пароль должен содержать минимум 1 специальный символ';
  return null;
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await api('GET', '/auth/me');
    window.location.replace('/board');
    return;
  } catch {
    // not logged in — show the form
  }

  const form        = document.getElementById('auth-form');
  const tabLogin    = document.getElementById('auth-tab-login');
  const tabReg      = document.getElementById('auth-tab-register');
  const submitBtn   = document.getElementById('auth-submit');
  const errorEl     = document.getElementById('auth-error');
  const emailEl     = document.getElementById('auth-email');
  const passwordEl  = document.getElementById('auth-password');
  const confirmWrap = document.getElementById('auth-confirm-wrap');
  const confirmEl   = document.getElementById('auth-confirm');
  const eyebrow     = document.getElementById('auth-eyebrow');
  const heading     = document.getElementById('auth-form-heading');
  const switchLabel = document.getElementById('auth-switch-label');
  const forgotWrap  = document.getElementById('auth-forgot-wrap');

  let mode = 'login';

  function setMode(m) {
    mode = m;
    const isReg = m === 'register';
    submitBtn.textContent     = isReg ? tA('btn-register') : tA('btn-login');
    confirmWrap.style.display = isReg ? '' : 'none';
    confirmEl.required        = isReg;
    eyebrow.textContent       = isReg ? 'Добро пожаловать' : 'С возвращением';
    heading.textContent       = isReg ? 'Создать аккаунт' : 'Войти в аккаунт';
    switchLabel.textContent   = isReg ? 'Уже есть аккаунт?' : 'Нет аккаунта?';
    tabLogin.style.display    = isReg ? '' : 'none';
    tabReg.style.display      = isReg ? 'none' : '';
    forgotWrap.style.display  = isReg ? 'none' : '';
    errorEl.textContent = '';
    form.reset();
  }

  bindPasswordToggles();

  if (new URLSearchParams(window.location.search).get('mode') === 'register') {
    setMode('register');
  }

  bindPasswordToggles();

  tabLogin.addEventListener('click', () => setMode('login'));
  tabReg.addEventListener('click',   () => setMode('register'));

  form.addEventListener('submit', async e => {
    e.preventDefault();
    errorEl.textContent = '';

    const email    = emailEl.value.trim();
    const password = passwordEl.value;

    const emailErr = validateEmail(email);
    if (emailErr) { errorEl.textContent = emailErr; return; }

    if (mode === 'register') {
      const pwErr = validatePassword(password);
      if (pwErr) { errorEl.textContent = pwErr; return; }
      if (password !== confirmEl.value) {
        errorEl.textContent = tA('passwords-mismatch'); return;
      }
    }

    submitBtn.disabled = true;
    try {
      const path = mode === 'login' ? '/auth/login' : '/auth/register';
      await api('POST', path, { email, password });
      window.location.replace('/board');
    } catch (err) {
      try {
        errorEl.textContent = JSON.parse(err.message).detail || 'Ошибка';
      } catch {
        errorEl.textContent = err.message || 'Ошибка';
      }
      submitBtn.disabled = false;
    }
  });
});
