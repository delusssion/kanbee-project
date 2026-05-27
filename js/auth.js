const API_BASE = '';

// ── Translations ────────────────────────────────────────────────────
const AUTH_LANG = {
  ru: {
    'btn-register':         'Зарегистрироваться →',
    'btn-login':            'Войти →',
    'passwords-mismatch':   'Пароли не совпадают',
    'eyebrow-login':        'С возвращением',
    'eyebrow-register':     'Добро пожаловать',
    'heading-login':        'Войти в аккаунт',
    'heading-register':     'Создать аккаунт',
    'switch-login':         'Нет аккаунта?',
    'switch-register':      'Уже есть аккаунт?',
    'tab-register':         'Зарегистрироваться',
    'tab-login':            'Войти',
    'label-email':          'Email',
    'label-password':       'Пароль',
    'label-confirm':        'Подтвердить пароль',
    'ph-email':             'Ваш email',
    'ph-password':          'Введите пароль',
    'ph-confirm':           'Повторите пароль',
    'forgot':               'Забыл пароль',
    'left-tagline':         'Задачи под <em>контролем</em>',
    'left-sub':             'Канбан-доска и трекер задач для командной работы. Просто, быстро, красиво.',
    'err_invalid_email':          'Некорректный email адрес',
    'err_email_taken':            'Этот email уже зарегистрирован',
    'err_wrong_credentials':      'Неверный email или пароль',
    'err_pwd_too_short':          'Пароль должен быть длиннее 8 символов',
    'err_pwd_no_letter':          'Пароль должен содержать хотя бы одну букву',
    'err_pwd_no_digits':          'Пароль должен содержать минимум 2 цифры',
    'err_pwd_no_special':         'Пароль должен содержать минимум 1 специальный символ',
    'err_email_send_failed':      'Не удалось отправить письмо. Попробуйте позже.',
    'err_reset_rate_limit':       'Подождите 2 минуты перед повторной отправкой кода',
    'err_invalid_code':           'Неверный или истёкший код',
    'err_code_attempts_exceeded': 'Превышено количество попыток. Запросите новый код',
    'err_user_not_found':         'Пользователь не найден',
    'err_pwd_reuse':              'Нельзя использовать ранее использованный пароль',
    'validate_email':             'Введите корректный email',
    'validate_pwd_short':         'Пароль должен быть длиннее 8 символов',
    'validate_pwd_letter':        'Пароль должен содержать хотя бы одну букву',
    'validate_pwd_digits':        'Пароль должен содержать минимум 2 цифры',
    'validate_pwd_special':       'Пароль должен содержать минимум 1 специальный символ',
  },
  en: {
    'btn-register':         'Create account →',
    'btn-login':            'Sign in →',
    'passwords-mismatch':   'Passwords do not match',
    'eyebrow-login':        'Welcome back',
    'eyebrow-register':     'Welcome',
    'heading-login':        'Sign in',
    'heading-register':     'Create account',
    'switch-login':         "Don't have an account?",
    'switch-register':      'Already have an account?',
    'tab-register':         'Sign up',
    'tab-login':            'Sign in',
    'label-email':          'Email',
    'label-password':       'Password',
    'label-confirm':        'Confirm password',
    'ph-email':             'Your email',
    'ph-password':          'Enter password',
    'ph-confirm':           'Repeat password',
    'forgot':               'Forgot password',
    'left-tagline':         'Tasks under <em>control</em>',
    'left-sub':             'Kanban board and task tracker for team and personal use. Simple, fast, beautiful.',
    'err_invalid_email':          'Invalid email address',
    'err_email_taken':            'This email is already registered',
    'err_wrong_credentials':      'Invalid email or password',
    'err_pwd_too_short':          'Password must be longer than 8 characters',
    'err_pwd_no_letter':          'Password must contain at least one letter',
    'err_pwd_no_digits':          'Password must contain at least 2 digits',
    'err_pwd_no_special':         'Password must contain at least 1 special character',
    'err_email_send_failed':      'Failed to send email. Please try again later.',
    'err_reset_rate_limit':       'Wait 2 minutes before requesting a new code',
    'err_invalid_code':           'Invalid or expired code',
    'err_code_attempts_exceeded': 'Too many attempts. Request a new code',
    'err_user_not_found':         'User not found',
    'err_pwd_reuse':              'You cannot reuse a previously used password',
    'validate_email':             'Enter a valid email',
    'validate_pwd_short':         'Password must be longer than 8 characters',
    'validate_pwd_letter':        'Password must contain at least one letter',
    'validate_pwd_digits':        'Password must contain at least 2 digits',
    'validate_pwd_special':       'Password must contain at least 1 special character',
  },
};

let authLang = localStorage.getItem('kanbee_lang') || 'ru';

function tA(key) {
  return (AUTH_LANG[authLang] && AUTH_LANG[authLang][key])
      || (AUTH_LANG['ru'] && AUTH_LANG['ru'][key])
      || key;
}

function tAErr(err) {
  try {
    const detail = JSON.parse(err.message).detail;
    if (typeof detail === 'string') return tA(detail);
    if (Array.isArray(detail) && detail.length > 0) return detail[0]?.msg || 'Error';
  } catch {}
  return err.message || 'Error';
}

// ── Password toggle ─────────────────────────────────────────────────
function bindPasswordToggles() {
  const eyeOpen = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
  const eyeOff  = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
  document.querySelectorAll('input[type="password"]').forEach(input => {
    if (input.parentNode.classList.contains('pwd-wrap')) return;
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

// ── API ──────────────────────────────────────────────────────────────
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

// ── Validation ───────────────────────────────────────────────────────
function validateEmail(email) {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return tA('validate_email');
  return null;
}

function validatePassword(password) {
  if (password.length <= 8) return tA('validate_pwd_short');
  if (!/[a-zA-Zа-яА-ЯёЁ]/.test(password)) return tA('validate_pwd_letter');
  if ((password.match(/\d/g) || []).length < 2) return tA('validate_pwd_digits');
  if (!/[^a-zA-Zа-яА-ЯёЁ\d]/.test(password)) return tA('validate_pwd_special');
  return null;
}

// ── Apply language to static DOM elements ────────────────────────────
function applyAuthLang(currentMode) {
  const taglineEl = document.getElementById('auth-left-tagline');
  const subEl     = document.getElementById('auth-left-sub');
  if (taglineEl) taglineEl.innerHTML = tA('left-tagline');
  if (subEl)     subEl.textContent   = tA('left-sub');

  const labelEmail   = document.getElementById('auth-label-email');
  const labelPwd     = document.getElementById('auth-label-password');
  const labelConfirm = document.getElementById('auth-label-confirm');
  if (labelEmail)   labelEmail.textContent   = tA('label-email');
  if (labelPwd)     labelPwd.textContent     = tA('label-password');
  if (labelConfirm) labelConfirm.textContent = tA('label-confirm');

  const emailInput   = document.getElementById('auth-email');
  const pwdInput     = document.getElementById('auth-password');
  const confirmInput = document.getElementById('auth-confirm');
  if (emailInput)   emailInput.placeholder   = tA('ph-email');
  if (pwdInput)     pwdInput.placeholder     = tA('ph-password');
  if (confirmInput) confirmInput.placeholder = tA('ph-confirm');

  const forgotEl = document.getElementById('auth-forgot');
  if (forgotEl) forgotEl.textContent = tA('forgot');

  const tabReg = document.getElementById('auth-tab-register');
  const tabLog = document.getElementById('auth-tab-login');
  if (tabReg) tabReg.textContent = tA('tab-register');
  if (tabLog) tabLog.textContent = tA('tab-login');

  document.querySelectorAll('.auth-lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === `auth-lang-${authLang}`);
  });

  if (currentMode) {
    const isReg = currentMode === 'register';
    const eyebrow     = document.getElementById('auth-eyebrow');
    const heading     = document.getElementById('auth-form-heading');
    const switchLabel = document.getElementById('auth-switch-label');
    const submitBtn   = document.getElementById('auth-submit');
    if (eyebrow)     eyebrow.textContent     = tA(isReg ? 'eyebrow-register' : 'eyebrow-login');
    if (heading)     heading.textContent     = tA(isReg ? 'heading-register' : 'heading-login');
    if (switchLabel) switchLabel.textContent = tA(isReg ? 'switch-register' : 'switch-login');
    if (submitBtn)   submitBtn.textContent   = tA(isReg ? 'btn-register' : 'btn-login');
  }
}

// ── Main ─────────────────────────────────────────────────────────────
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
  const forgotWrap  = document.getElementById('auth-forgot-wrap');

  let mode = 'login';

  function setMode(m) {
    mode = m;
    const isReg = m === 'register';
    confirmWrap.style.display = isReg ? '' : 'none';
    confirmEl.required        = isReg;
    tabLogin.style.display    = isReg ? '' : 'none';
    tabReg.style.display      = isReg ? 'none' : '';
    forgotWrap.style.display  = isReg ? 'none' : '';
    errorEl.textContent = '';
    form.reset();
    applyAuthLang(m);
    bindPasswordToggles();
  }

  bindPasswordToggles();
  applyAuthLang(mode);

  if (new URLSearchParams(window.location.search).get('mode') === 'register') {
    setMode('register');
  }

  tabLogin.addEventListener('click', () => setMode('login'));
  tabReg.addEventListener('click',   () => setMode('register'));

  const langRuBtn = document.getElementById('auth-lang-ru');
  const langEnBtn = document.getElementById('auth-lang-en');
  if (langRuBtn) langRuBtn.addEventListener('click', () => {
    authLang = 'ru';
    localStorage.setItem('kanbee_lang', 'ru');
    applyAuthLang(mode);
  });
  if (langEnBtn) langEnBtn.addEventListener('click', () => {
    authLang = 'en';
    localStorage.setItem('kanbee_lang', 'en');
    applyAuthLang(mode);
  });

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
      errorEl.textContent = tAErr(err);
      submitBtn.disabled = false;
    }
  });
});
