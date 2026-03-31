const API_BASE = '';

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

document.addEventListener('DOMContentLoaded', async () => {
  // If already logged in, go straight to the board
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
  const usernameEl  = document.getElementById('auth-username');
  const passwordEl  = document.getElementById('auth-password');
  const confirmWrap = document.getElementById('auth-confirm-wrap');
  const confirmEl   = document.getElementById('auth-confirm');
  const eyebrow     = document.getElementById('auth-eyebrow');
  const heading     = document.getElementById('auth-form-heading');
  const switchLabel = document.getElementById('auth-switch-label');

  let mode = 'login';

  function setMode(m) {
    mode = m;
    const isReg = m === 'register';
    submitBtn.textContent     = isReg ? 'Зарегистрироваться →' : 'Войти →';
    confirmWrap.style.display = isReg ? '' : 'none';
    confirmEl.required        = isReg;
    passwordEl.placeholder    = isReg ? 'Минимум 8 символов' : 'Введите пароль';
    eyebrow.textContent       = isReg ? 'Добро пожаловать' : 'С возвращением';
    heading.textContent       = isReg ? 'Создать аккаунт' : 'Войти в аккаунт';
    switchLabel.textContent   = isReg ? 'Уже есть аккаунт?' : 'Нет аккаунта?';
    tabLogin.style.display    = isReg ? '' : 'none';
    tabReg.style.display      = isReg ? 'none' : '';
    errorEl.textContent = '';
    form.reset();
  }

  // Check URL param to open register mode directly
  if (new URLSearchParams(window.location.search).get('mode') === 'register') {
    setMode('register');
  }

  tabLogin.addEventListener('click', () => setMode('login'));
  tabReg.addEventListener('click',   () => setMode('register'));

  form.addEventListener('submit', async e => {
    e.preventDefault();
    errorEl.textContent = '';
    const username = usernameEl.value.trim();
    const password = passwordEl.value;

    if (mode === 'register') {
      if (username.length < 5) {
        errorEl.textContent = 'Логин должен содержать минимум 5 символов'; return;
      }
      if (password.length < 8) {
        errorEl.textContent = 'Пароль должен содержать минимум 8 символов'; return;
      }
      if (!/[a-zA-Zа-яА-Я]/.test(password)) {
        errorEl.textContent = 'Пароль должен содержать хотя бы одну букву'; return;
      }
      if (!/\d/.test(password)) {
        errorEl.textContent = 'Пароль должен содержать хотя бы одну цифру'; return;
      }
      if (password !== confirmEl.value) {
        errorEl.textContent = 'Пароли не совпадают'; return;
      }
    }

    try {
      const path = mode === 'login' ? '/auth/login' : '/auth/register';
      await api('POST', path, { username, password });
      window.location.replace('/board');
    } catch (err) {
      try {
        errorEl.textContent = JSON.parse(err.message).detail || 'Ошибка';
      } catch {
        errorEl.textContent = err.message || 'Ошибка';
      }
    }
  });
});
