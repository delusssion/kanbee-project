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

  const form      = document.getElementById('reset-form');
  const submitBtn = document.getElementById('reset-submit');
  const errorEl   = document.getElementById('reset-error');
  const usernameEl = document.getElementById('reset-username');
  const passwordEl = document.getElementById('reset-password');
  const confirmEl  = document.getElementById('reset-confirm');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    errorEl.style.color = '';
    errorEl.textContent = '';

    const username = usernameEl.value.trim();
    const password = passwordEl.value;
    const confirm  = confirmEl.value;

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
    if (password !== confirm) {
      errorEl.textContent = 'Пароли не совпадают'; return;
    }

    submitBtn.disabled = true;
    try {
      await api('POST', '/auth/reset-password', { username, new_password: password });
      errorEl.style.color = 'var(--done)';
      errorEl.textContent = 'Пароль успешно изменён. Перенаправление...';
      setTimeout(() => window.location.replace('/registration'), 1500);
    } catch (err) {
      try { errorEl.textContent = JSON.parse(err.message).detail || 'Ошибка'; }
      catch { errorEl.textContent = err.message || 'Ошибка'; }
      submitBtn.disabled = false;
    }
  });
});
