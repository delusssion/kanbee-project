const API_BASE = '';

const AUTH_I18N = {
  en: {
    'welcome':            'Welcome',
    'sign-in-back':       'Welcome back',
    'create-account':     'Create account',
    'sign-in-heading':    'Sign in to your account',
    'already-have':       'Already have an account?',
    'no-account':         'Don\'t have an account?',
    'btn-register':       'Create account →',
    'btn-login':          'Sign in →',
    'passwords-mismatch': 'Passwords do not match',
    'err-generic':        'Something went wrong',
    'err_username_too_short':  'Username must be at least 5 characters',
    'err_username_taken':      'This username is already taken',
    'err_pwd_too_short':       'Password must be at least 8 characters',
    'err_pwd_no_letter':       'Password must contain at least one letter',
    'err_pwd_no_digits':       'Password must contain at least one digit',
    'err_wrong_credentials':   'Invalid username or password',
    'err_user_not_found':      'User not found',
    'err_wrong_current_password': 'Incorrect current password',
  },
  ru: {
    'welcome':            'Добро пожаловать',
    'sign-in-back':       'С возвращением',
    'create-account':     'Создать аккаунт',
    'sign-in-heading':    'Войти в аккаунт',
    'already-have':       'Уже есть аккаунт?',
    'no-account':         'Нет аккаунта?',
    'btn-register':       'Зарегистрироваться →',
    'btn-login':          'Войти →',
    'passwords-mismatch': 'Пароли не совпадают',
    'err-generic':        'Что-то пошло не так',
    'err_username_too_short':  'Логин должен содержать минимум 5 символов',
    'err_username_taken':      'Этот логин уже занят',
    'err_pwd_too_short':       'Пароль должен содержать минимум 8 символов',
    'err_pwd_no_letter':       'Пароль должен содержать хотя бы одну букву',
    'err_pwd_no_digits':       'Пароль должен содержать хотя бы одну цифру',
    'err_wrong_credentials':   'Неверный логин или пароль',
    'err_user_not_found':      'Пользователь не найден',
    'err_wrong_current_password': 'Неверный текущий пароль',
  },
};

const authLang = localStorage.getItem('kanbee_lang') || 'ru';
function tA(key) {
  return (AUTH_I18N[authLang] && AUTH_I18N[authLang][key]) || AUTH_I18N.en[key] || key;
}
function tAErr(err) {
  try {
    const detail = JSON.parse(err.message).detail;
    const code = typeof detail === 'string' ? detail : null;
    if (code && AUTH_I18N.en[code]) return tA(code);
  } catch {}
  return err.message || tA('err-generic');
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
  const usernameEl  = document.getElementById('auth-username');
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
    eyebrow.textContent       = isReg ? tA('welcome') : tA('sign-in-back');
    heading.textContent       = isReg ? tA('create-account') : tA('sign-in-heading');
    switchLabel.textContent   = isReg ? tA('already-have') : tA('no-account');
    tabLogin.style.display    = isReg ? '' : 'none';
    tabReg.style.display      = isReg ? 'none' : '';
    forgotWrap.style.display  = isReg ? 'none' : '';
    errorEl.textContent = '';
    form.reset();
  }

  if (new URLSearchParams(window.location.search).get('mode') === 'register') {
    setMode('register');
  }

  bindPasswordToggles();

  tabLogin.addEventListener('click', () => setMode('login'));
  tabReg.addEventListener('click',   () => setMode('register'));

  form.addEventListener('submit', async e => {
    e.preventDefault();
    errorEl.textContent = '';
    const username = usernameEl.value.trim();
    const password = passwordEl.value;

    if (mode === 'register') {
      if (username.length < 5) {
        errorEl.textContent = tA('err_username_too_short'); return;
      }
      if (password.length < 8) {
        errorEl.textContent = tA('err_pwd_too_short'); return;
      }
      if (!/[a-zA-Zа-яА-ЯёЁ]/.test(password)) {
        errorEl.textContent = tA('err_pwd_no_letter'); return;
      }
      if (!/\d/.test(password)) {
        errorEl.textContent = tA('err_pwd_no_digits'); return;
      }
      if (password !== confirmEl.value) {
        errorEl.textContent = tA('passwords-mismatch'); return;
      }
    }

    submitBtn.disabled = true;
    try {
      const path = mode === 'login' ? '/auth/login' : '/auth/register';
      await api('POST', path, { username, password });
      window.location.replace('/board');
    } catch (err) {
      errorEl.textContent = tAErr(err);
      submitBtn.disabled = false;
    }
  });
});
