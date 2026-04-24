// ── API ────────────────────────────────────────────────────────────
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

// ── State ──────────────────────────────────────────────────────────
let tasks = [];
let dragSrcId = null;
let lang = 'en';
let currentView = 'kanban';
let userName = '';
let defaultView = 'kanban';

// ── Init ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const user = await checkAuth();
  if (!user) return;
  await initApp();
});

async function checkAuth() {
  try {
    const user = await api('GET', '/auth/me');
    userName = user.username;
    return user;
  } catch {
    window.location.replace('/registration');
    return null;
  }
}

async function initApp() {
  await loadSettings();
  applyDefaultView();
  bindNav();
  bindModal();
  bindTracker();
  bindGroups();
  bindDateAutoAdvance();
  bindProfileDropdown();
  bindSettings();
  bindConfirm();
  await refreshTasks();
}

async function loadSettings() {
  const s = await api('GET', '/settings');
  lang        = s.lang         || 'en';
  defaultView = s.default_view || 'kanban';
  document.documentElement.dataset.theme = s.theme || 'dark';
  applyLang();
}


async function refreshTasks() {
  tasks = await api('GET', '/tasks');
  render();
}

// ── Translations ───────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    'signin':                 'Sign in',
    'signout':                'Sign out',
    'confirm-title':          'Are you sure?',
    'confirm-delete':         'Delete',
    'settings':               'Settings',
    'settings-account':       'Account',
    'settings-appearance':    'Appearance',
    'settings-prefs':         'Preferences',
    'settings-data':          'Data',
    'settings-lang':          'Language',
    'settings-theme':         'Theme',
    'settings-default-view':  'Default view',
    'settings-export':        'Export JSON',
    'settings-import':        'Import JSON',
    'settings-clear':         'Clear all tasks',
    'settings-guest':         'Guest',
    'settings-local-profile': 'Local profile',
    'settings-edit':          'Edit',
    'settings-save':          'Save',
    'settings-name-ph':       'Your name',
    'settings-confirm-clear': 'Delete all tasks? This cannot be undone.',
    'settings-confirm-delete-task': 'Do you really want to delete this task? This action cannot be undone.',
    'settings-change-pwd':     'Change password',
    'settings-pwd-current-ph': 'Current password',
    'settings-pwd-new-ph':     'New password (8+ chars, letter + digit)',
    'settings-pwd-success':    'Password changed',
    'nav-kanban':          'Kanban Board',
    'nav-tracker':         'Task Tracker',
    'subtitle-kanban':     'Drag cards between columns to update status',
    'subtitle-tracker':    'Filter, search and manage all tasks',
    'btn-new-task':        'New Task',
    'col-todo':            'To Do',
    'col-inprocess':       'In Process',
    'col-done':            'Done',
    'add-card':            '+ Add task',
    'search-ph':           'Search tasks...',
    'filter-all':          'All',
    'filter-all-status':   'All Statuses',
    'filter-all-priority': 'All Priorities',
    'pri-high':            'High',
    'pri-medium':          'Medium',
    'pri-low':             'Low',
    'th-task':             'Task',
    'th-status':           'Status',
    'th-priority':         'Priority',
    'th-due':              'Due Date',
    'th-actions':          'Actions',
    'empty-text':          'No tasks yet. Create your first task.',
    'modal-new':           'New Task',
    'modal-edit':          'Edit Task',
    'lbl-title':           'Title',
    'lbl-desc':            'Description',
    'lbl-status':          'Status',
    'lbl-priority':        'Priority',
    'lbl-due':             'Due Date',
    'ph-title':            'Task title',
    'ph-desc':             'Optional description...',
    'btn-cancel':          'Cancel',
    'btn-create':          'Create Task',
    'btn-save':            'Save Changes',
    'theme-light':         'Light',
    'theme-dark':          'Dark',
  },
  ru: {
    'signin':                 'Войти',
    'signout':                'Выйти',
    'confirm-title':          'Вы уверены?',
    'confirm-delete':         'Удалить',
    'settings':               'Настройки',
    'settings-account':       'Аккаунт',
    'settings-appearance':    'Внешний вид',
    'settings-prefs':         'Настройки',
    'settings-data':          'Данные',
    'settings-lang':          'Язык',
    'settings-theme':         'Тема',
    'settings-default-view':  'Вид по умолчанию',
    'settings-export':        'Экспорт JSON',
    'settings-import':        'Импорт JSON',
    'settings-clear':         'Очистить задачи',
    'settings-guest':         'Гость',
    'settings-local-profile': 'Локальный профиль',
    'settings-edit':          'Изменить',
    'settings-save':          'Сохранить',
    'settings-name-ph':       'Ваше имя',
    'settings-confirm-clear': 'Удалить все задачи? Это необратимо.',
    'settings-confirm-delete-task': 'Вы действительно хотите удалить данную задачу? Это действие нельзя отменить.',
    'settings-change-pwd':     'Сменить пароль',
    'settings-pwd-current-ph': 'Текущий пароль',
    'settings-pwd-new-ph':     'Новый пароль (8+ симв., буква и цифра)',
    'settings-pwd-success':    'Пароль изменён',
    'nav-kanban':          'Канбан-доска',
    'nav-tracker':         'Трекер задач',
    'subtitle-kanban':     'Перетащите карточки между колонками для смены статуса',
    'subtitle-tracker':    'Фильтрация, поиск и управление задачами',
    'btn-new-task':        'Новая задача',
    'col-todo':            'К выполнению',
    'col-inprocess':       'В работе',
    'col-done':            'Готово',
    'add-card':            '+ Добавить',
    'search-ph':           'Поиск задач...',
    'filter-all':          'Все',
    'filter-all-status':   'Все статусы',
    'filter-all-priority': 'Все приоритеты',
    'pri-high':            'Высокий',
    'pri-medium':          'Средний',
    'pri-low':             'Низкий',
    'th-task':             'Задача',
    'th-status':           'Статус',
    'th-priority':         'Приоритет',
    'th-due':              'Срок',
    'th-actions':          'Действия',
    'empty-text':          'Задач пока нет. Создайте первую задачу.',
    'modal-new':           'Новая задача',
    'modal-edit':          'Редактировать',
    'lbl-title':           'Название',
    'lbl-desc':            'Описание',
    'lbl-status':          'Статус',
    'lbl-priority':        'Приоритет',
    'lbl-due':             'Срок',
    'ph-title':            'Название задачи',
    'ph-desc':             'Необязательное описание...',
    'btn-cancel':          'Отмена',
    'btn-create':          'Создать',
    'btn-save':            'Сохранить',
    'theme-light':         'Светлая',
    'theme-dark':          'Тёмная',
  },
};

function t(key) {
  return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS.en[key] || key;
}

// ── Language ───────────────────────────────────────────────────────
function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPh);
  });
  document.getElementById('view-title').textContent =
    t(currentView === 'kanban' ? 'nav-kanban' : 'nav-tracker');
  document.getElementById('view-subtitle').textContent =
    t(currentView === 'kanban' ? 'subtitle-kanban' : 'subtitle-tracker');
  updateProfileUI();
}

// ── Segmented group helpers ─────────────────────────────────────────
function setGroupValue(groupId, value) {
  const group = document.getElementById(groupId);
  group.querySelectorAll('.seg-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.value === value);
  });
  document.getElementById(group.dataset.input).value = value;
}

function bindGroups() {
  document.querySelectorAll('.seg-group').forEach(group => {
    group.querySelectorAll('.seg-btn').forEach(btn => {
      btn.addEventListener('click', () => setGroupValue(group.id, btn.dataset.value));
    });
  });
}

// ── Date parts helpers ──────────────────────────────────────────────
function setDateParts(iso) {
  if (iso) {
    const [y, m, d] = iso.split('-');
    document.getElementById('task-due-day').value   = parseInt(d, 10);
    document.getElementById('task-due-month').value = parseInt(m, 10);
    document.getElementById('task-due-year').value  = y;
  } else {
    document.getElementById('task-due-day').value   = '';
    document.getElementById('task-due-month').value = '';
    document.getElementById('task-due-year').value  = '';
  }
}

function getDateFromParts() {
  const d = document.getElementById('task-due-day').value;
  const m = document.getElementById('task-due-month').value;
  const y = document.getElementById('task-due-year').value;
  if (!d || !m || !y) return '';
  return `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}

function bindDateAutoAdvance() {
  const day   = document.getElementById('task-due-day');
  const month = document.getElementById('task-due-month');
  const year  = document.getElementById('task-due-year');
  day.addEventListener('input', () => { if (day.value.length >= 2) month.focus(); });
  month.addEventListener('input', () => { if (month.value.length >= 2) year.focus(); });
}

// ── Render ─────────────────────────────────────────────────────────
function render() {
  renderKanban();
  renderTracker();
  updateSidebar();
}

function renderKanban() {
  ['todo', 'inprocess', 'done'].forEach(status => {
    const list  = document.getElementById('list-' + status);
    const badge = document.getElementById('badge-' + status);
    const col   = tasks.filter(t => t.status === status);
    badge.textContent = col.length;
    list.innerHTML = '';
    col.forEach(t => list.appendChild(createCard(t)));
    bindDrop(list, status);
  });
}

function createCard(task) {
  const card = document.createElement('div');
  card.className = 'card';
  card.draggable = true;
  card.dataset.id = task.id;

  const dueHtml = task.due
    ? `<span class="card-due ${dueCls(task.due)}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8"  y1="2" x2="8"  y2="6"/>
          <line x1="3"  y1="10" x2="21" y2="10"/>
        </svg>
        ${formatDate(task.due)}
      </span>`
    : '';

  const descHtml = task.desc
    ? `<p class="card-desc">${escHtml(task.desc)}</p>`
    : '';

  card.innerHTML = `
    <div class="card-top">
      <span class="card-title">${escHtml(task.title)}</span>
      <div class="card-actions">
        <button class="card-action-btn edit" title="${t('modal-edit')}" data-id="${task.id}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button class="card-action-btn delete" title="Delete" data-id="${task.id}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
            <path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
          </svg>
        </button>
      </div>
    </div>
    ${descHtml}
    <div class="card-footer">
      <span class="priority-badge priority-${task.priority}">
        ${priorityIcon(task.priority)}${t('pri-' + task.priority)}
      </span>
      ${dueHtml}
    </div>
  `;

  card.addEventListener('dragstart', () => {
    dragSrcId = task.id;
    setTimeout(() => card.classList.add('dragging'), 0);
  });
  card.addEventListener('dragend', () => {
    card.classList.remove('dragging');
    dragSrcId = null;
    document.querySelectorAll('.card-list').forEach(l => l.classList.remove('drag-over'));
  });

  addTouchDrag(card, task.id);

  card.querySelector('.edit').addEventListener('click', () => openModal(task));
  card.querySelector('.delete').addEventListener('click', () => deleteTask(task.id));

  return card;
}

function addTouchDrag(card, taskId) {
  let startX, startY, ghost = null, activeList = null, moved = false;
  const THRESHOLD = 10;

  card.addEventListener('touchstart', e => {
    const touch = e.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    moved = false;
  }, { passive: true });

  card.addEventListener('touchmove', e => {
    if (!e.touches.length) return;
    const touch = e.touches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;

    if (!ghost && Math.hypot(dx, dy) > THRESHOLD) {
      moved = true;
      const rect = card.getBoundingClientRect();
      ghost = card.cloneNode(true);
      Object.assign(ghost.style, {
        position: 'fixed',
        width: rect.width + 'px',
        left: rect.left + 'px',
        top: rect.top + 'px',
        opacity: '0.88',
        pointerEvents: 'none',
        zIndex: '9999',
        transform: 'scale(1.04) rotate(1deg)',
        boxShadow: '0 12px 40px rgba(0,0,0,0.35)',
        transition: 'none',
        borderRadius: '12px',
      });
      document.body.appendChild(ghost);
      card.style.opacity = '0.25';
      dragSrcId = taskId;
    }

    if (ghost) {
      e.preventDefault();
      const touch2 = e.touches[0];
      const rect = card.getBoundingClientRect();
      ghost.style.left = (touch2.clientX - rect.width / 2) + 'px';
      ghost.style.top  = (touch2.clientY - 40) + 'px';

      ghost.style.display = 'none';
      const el = document.elementFromPoint(touch2.clientX, touch2.clientY);
      ghost.style.display = '';

      const listEl = el?.closest('.cards-list');
      document.querySelectorAll('.cards-list').forEach(l => l.classList.remove('drag-over'));
      if (listEl) { listEl.classList.add('drag-over'); activeList = listEl; }
      else activeList = null;
    }
  }, { passive: false });

  card.addEventListener('touchend', async () => {
    if (ghost) {
      ghost.remove();
      ghost = null;
      card.style.opacity = '';
      document.querySelectorAll('.cards-list').forEach(l => l.classList.remove('drag-over'));

      if (activeList && dragSrcId) {
        const status = activeList.dataset.status;
        const task = tasks.find(t => t.id === dragSrcId);
        if (task && task.status !== status) {
          const updated = await api('PATCH', `/tasks/${task.id}`, { status });
          const idx = tasks.findIndex(t => t.id === task.id);
          if (idx !== -1) tasks[idx] = updated;
          render();
        }
      }
      dragSrcId = null;
      activeList = null;
    }
  });
}

function bindDrop(list, status) {
  list.addEventListener('dragover', e => {
    e.preventDefault();
    list.classList.add('drag-over');
  });
  list.addEventListener('dragleave', () => list.classList.remove('drag-over'));
  list.addEventListener('drop', async e => {
    e.preventDefault();
    list.classList.remove('drag-over');
    if (dragSrcId) {
      const task = tasks.find(t => t.id === dragSrcId);
      if (task && task.status !== status) {
        const updated = await api('PATCH', `/tasks/${task.id}`, { status });
        const idx = tasks.findIndex(t => t.id === task.id);
        if (idx !== -1) tasks[idx] = updated;
        render();
      }
    }
  });
}

// ── Tracker ────────────────────────────────────────────────────────
function renderTracker(filter = {}) {
  const body  = document.getElementById('tracker-body');
  const empty = document.getElementById('tracker-empty');

  const filtered = tasks.filter(task => {
    const q = (filter.query || '').toLowerCase();
    if (q && !task.title.toLowerCase().includes(q) && !(task.desc || '').toLowerCase().includes(q)) return false;
    if (filter.status   && task.status   !== filter.status)   return false;
    if (filter.priority && task.priority !== filter.priority) return false;
    return true;
  });

  if (filtered.length === 0) {
    body.innerHTML = '';
    empty.style.display = 'flex';
    return;
  }

  empty.style.display = 'none';
  body.innerHTML = filtered.map(task => {
    const dueClass = dueCls(task.due);
    return `
      <tr>
        <td>
          <div class="task-name-cell">${escHtml(task.title)}</div>
          ${task.desc ? `<div class="task-desc-cell">${escHtml(task.desc)}</div>` : ''}
        </td>
        <td>
          <span class="status-badge status-${task.status}">
            <span class="status-dot" style="background:var(--${task.status})"></span>
            ${statusLabel(task.status)}
          </span>
        </td>
        <td>
          <span class="priority-badge priority-${task.priority}">
            ${priorityIcon(task.priority)}${t('pri-' + task.priority)}
          </span>
        </td>
        <td class="due-cell ${dueClass}">${task.due ? formatDate(task.due) : '—'}</td>
        <td>
          <div class="table-actions">
            <button class="tbl-btn" title="${t('modal-edit')}" onclick="openModal(tasks.find(x=>x.id==='${task.id}'))">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="tbl-btn delete" onclick="deleteTask('${task.id}')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

function bindTracker() {
  const searchInput = document.getElementById('search-input');
  let statusFilter   = '';
  let priorityFilter = '';

  function applyFilter() {
    renderTracker({ query: searchInput.value, status: statusFilter, priority: priorityFilter });
  }

  searchInput.addEventListener('input', applyFilter);

  function bindFilterDrop(wrapId, menuId, labelId, onSelect) {
    const wrap  = document.getElementById(wrapId);
    const menu  = document.getElementById(menuId);
    const label = document.getElementById(labelId);
    const btn   = wrap.querySelector('.filter-drop-btn');

    btn.addEventListener('click', e => {
      e.stopPropagation();
      document.querySelectorAll('.filter-drop-wrap.open').forEach(w => { if (w !== wrap) w.classList.remove('open'); });
      wrap.classList.toggle('open');
    });

    menu.querySelectorAll('.filter-menu-item').forEach(item => {
      item.addEventListener('click', () => {
        menu.querySelectorAll('.filter-menu-item').forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');

        const val     = item.dataset.value;
        const i18nKey = item.dataset.labelI18n;
        label.dataset.i18n = i18nKey;
        label.textContent  = t(i18nKey);
        btn.classList.toggle('active', val !== '');

        wrap.classList.remove('open');
        onSelect(val);
      });
    });
  }

  bindFilterDrop('status-drop-wrap',   'status-drop-menu',   'status-drop-label',   v => { statusFilter   = v; applyFilter(); });
  bindFilterDrop('priority-drop-wrap', 'priority-drop-menu', 'priority-drop-label', v => { priorityFilter = v; applyFilter(); });

  document.addEventListener('click', () => {
    document.querySelectorAll('.filter-drop-wrap.open').forEach(w => w.classList.remove('open'));
  });
}

function updateSidebar() {
  ['todo', 'inprocess', 'done'].forEach(s => {
    document.getElementById('count-' + s).textContent = tasks.filter(t => t.status === s).length;
  });
}

// ── Modal ──────────────────────────────────────────────────────────
function openModal(task = null) {
  const overlay = document.getElementById('modal-overlay');
  const titleEl = document.getElementById('modal-title');
  const submitEl = document.getElementById('modal-submit');
  const form = document.getElementById('task-form');

  form.reset();
  if (task) {
    titleEl.textContent  = t('modal-edit');
    submitEl.textContent = t('btn-save');
    titleEl.dataset.i18n  = 'modal-edit';
    submitEl.dataset.i18n = 'btn-save';
    document.getElementById('task-id').value    = task.id;
    document.getElementById('task-title').value = task.title;
    document.getElementById('task-desc').value  = task.desc || '';
    setGroupValue('status-group',   task.status);
    setGroupValue('priority-group', task.priority);
    setDateParts(task.due);
  } else {
    titleEl.textContent  = t('modal-new');
    submitEl.textContent = t('btn-create');
    titleEl.dataset.i18n  = 'modal-new';
    submitEl.dataset.i18n = 'btn-create';
    document.getElementById('task-id').value = '';
    setGroupValue('status-group',   'todo');
    setGroupValue('priority-group', 'medium');
    setDateParts('');
  }

  overlay.classList.add('open');
  if (window.innerWidth > 768) document.getElementById('task-title').focus();
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}

function bindModal() {
  document.getElementById('add-task-btn').addEventListener('click', () => openModal());
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-cancel').addEventListener('click', closeModal);
  document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
  });

  document.querySelectorAll('.add-card-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      openModal();
      setGroupValue('status-group', btn.dataset.status);
    });
  });

  document.getElementById('task-form').addEventListener('submit', async e => {
    e.preventDefault();
    const id = document.getElementById('task-id').value;
    const data = {
      title:    document.getElementById('task-title').value.trim(),
      desc:     document.getElementById('task-desc').value.trim(),
      status:   document.getElementById('task-status').value,
      priority: document.getElementById('task-priority').value,
      due:      getDateFromParts(),
    };
    if (!data.title) return;

    if (id) {
      const updated = await api('PATCH', `/tasks/${id}`, data);
      const idx = tasks.findIndex(t => t.id === id);
      if (idx !== -1) tasks[idx] = updated;
    } else {
      const created = await api('POST', '/tasks', data);
      tasks.push(created);
    }

    render();
    closeModal();
  });

  document.getElementById('clear-all-btn').addEventListener('click', () => {
    showConfirm(t('settings-confirm-clear'), async () => {
      await Promise.all(tasks.map(t => api('DELETE', `/tasks/${t.id}`)));
      tasks = [];
      render();
    });
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
}

// ── Nav ────────────────────────────────────────────────────────────
function bindNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentView = btn.dataset.view;
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      document.getElementById('view-' + currentView).classList.add('active');
      document.getElementById('view-title').textContent =
        t(currentView === 'kanban' ? 'nav-kanban' : 'nav-tracker');
      document.getElementById('view-subtitle').textContent =
        t(currentView === 'kanban' ? 'subtitle-kanban' : 'subtitle-tracker');
      if (currentView === 'tracker') renderTracker();
    });
  });
}

// ── Task actions ───────────────────────────────────────────────────
async function deleteTask(id) {
  showConfirm(t('settings-confirm-delete-task'), async () => {
    await api('DELETE', `/tasks/${id}`);
    tasks = tasks.filter(t => t.id !== id);
    render();
  });
}

// ── Helpers ────────────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function dueCls(iso) {
  if (!iso) return '';
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const due = new Date(iso);
  if (due < today) return 'overdue';
  const diff = (due - today) / (1000 * 60 * 60 * 24);
  if (diff <= 2) return 'soon';
  return '';
}

function statusLabel(s) {
  return { todo: t('col-todo'), inprocess: t('col-inprocess'), done: t('col-done') }[s] || s;
}

function priorityIcon(p) {
  return {
    high:   '<svg viewBox="0 0 10 10"><polygon points="5,1 9,9 1,9" fill="currentColor"/></svg>',
    medium: '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="currentColor"/></svg>',
    low:    '<svg viewBox="0 0 10 10"><polygon points="5,9 9,1 1,1" fill="currentColor"/></svg>',
  }[p] || '';
}

function escHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Default View ────────────────────────────────────────────────────
function applyDefaultView() {
  if (defaultView === 'tracker') {
    currentView = 'tracker';
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-view="tracker"]').classList.add('active');
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view-tracker').classList.add('active');
  }
}

// ── Settings ────────────────────────────────────────────────────────
function openSettings() {
  syncSettingsUI();
  document.getElementById('settings-user-name').textContent = userName;
  document.getElementById('settings-user-avatar').textContent = userName ? userName[0].toUpperCase() : '';
  document.getElementById('settings-pwd-form').classList.remove('open');
  document.getElementById('settings-pwd-current').value = '';
  document.getElementById('settings-pwd-new').value = '';
  document.getElementById('settings-pwd-error').textContent = '';
  document.getElementById('settings-overlay').classList.add('open');
}

function closeSettings() {
  document.getElementById('settings-overlay').classList.remove('open');
}

function syncSettingsUI() {
  document.querySelectorAll('#lang-seg .settings-seg-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  const currentTheme = document.documentElement.dataset.theme;
  document.querySelectorAll('#theme-seg .settings-seg-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.themeVal === currentTheme);
  });

  document.querySelectorAll('#defview-seg .settings-seg-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.defview === defaultView);
  });
}

function bindSettings() {
  document.getElementById('settings-close').addEventListener('click', closeSettings);
  document.getElementById('settings-overlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeSettings();
  });

  document.querySelectorAll('#lang-seg .settings-seg-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      lang = btn.dataset.lang;
      await api('PATCH', '/settings', { lang });
      applyLang();
      render();
      syncSettingsUI();
    });
  });

  document.querySelectorAll('#theme-seg .settings-seg-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const theme = btn.dataset.themeVal;
      document.documentElement.dataset.theme = theme;
      await api('PATCH', '/settings', { theme });
      document.querySelectorAll('#theme-seg .settings-seg-btn').forEach(b => {
        b.classList.toggle('active', b === btn);
      });
    });
  });

  document.querySelectorAll('#defview-seg .settings-seg-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      defaultView = btn.dataset.defview;
      await api('PATCH', '/settings', { default_view: defaultView });
      document.querySelectorAll('#defview-seg .settings-seg-btn').forEach(b => {
        b.classList.toggle('active', b === btn);
      });
    });
  });

  // Change password
  document.getElementById('settings-pwd-btn').addEventListener('click', () => {
    document.getElementById('settings-pwd-form').classList.toggle('open');
  });
  document.getElementById('settings-pwd-cancel').addEventListener('click', () => {
    document.getElementById('settings-pwd-form').classList.remove('open');
    document.getElementById('settings-pwd-error').textContent = '';
  });
  document.getElementById('settings-pwd-save').addEventListener('click', async () => {
    const current = document.getElementById('settings-pwd-current').value;
    const next    = document.getElementById('settings-pwd-new').value;
    const errEl   = document.getElementById('settings-pwd-error');
    errEl.style.color = '';
    errEl.textContent = '';
    if (!current || !next) { errEl.textContent = 'Заполните оба поля'; return; }
    try {
      await api('POST', '/auth/change-password', { current_password: current, new_password: next });
      errEl.style.color = 'var(--done)';
      errEl.textContent = t('settings-pwd-success');
      setTimeout(() => {
        document.getElementById('settings-pwd-form').classList.remove('open');
        errEl.textContent = ''; errEl.style.color = '';
      }, 1500);
    } catch (err) {
      try { errEl.textContent = JSON.parse(err.message).detail || 'Ошибка'; }
      catch { errEl.textContent = err.message || 'Ошибка'; }
    }
  });
}

// ── Profile UI ──────────────────────────────────────────────────────
function updateProfileUI() {
  const nameEl    = document.getElementById('profile-name');
  const avatarEl  = document.getElementById('profile-avatar');
  const authLabel = document.getElementById('dropdown-auth-label');

  nameEl.textContent = userName;
  avatarEl.innerHTML = userName[0].toUpperCase();
  avatarEl.classList.add('has-name');
  if (authLabel) authLabel.textContent = t('signout');
}

// ── Profile Dropdown ────────────────────────────────────────────────
function bindProfileDropdown() {
  const area     = document.getElementById('profile-area');
  const btn      = document.getElementById('profile-btn');
  const dropdown = document.getElementById('profile-dropdown');

  updateProfileUI();

  btn.addEventListener('click', e => {
    e.stopPropagation();
    area.classList.toggle('open');
  });

  document.addEventListener('click', () => area.classList.remove('open'));
  dropdown.addEventListener('click', e => e.stopPropagation());

  document.getElementById('dropdown-auth-btn').addEventListener('click', async () => {
    await api('POST', '/auth/logout');
    window.location.replace('/registration');
  });

  document.getElementById('dropdown-open-settings').addEventListener('click', () => {
    area.classList.remove('open');
    openSettings();
  });
}

// ── Custom Confirm ──────────────────────────────────────────────────
let _confirmCallback = null;

function showConfirm(message, onConfirm) {
  document.getElementById('confirm-message').textContent = message;
  document.getElementById('confirm-overlay').classList.add('open');
  _confirmCallback = onConfirm;
}

function bindConfirm() {
  document.getElementById('confirm-ok-btn').addEventListener('click', () => {
    document.getElementById('confirm-overlay').classList.remove('open');
    if (_confirmCallback) { _confirmCallback(); _confirmCallback = null; }
  });
  document.getElementById('confirm-cancel-btn').addEventListener('click', () => {
    document.getElementById('confirm-overlay').classList.remove('open');
    _confirmCallback = null;
  });
  document.getElementById('confirm-overlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) {
      document.getElementById('confirm-overlay').classList.remove('open');
      _confirmCallback = null;
    }
  });
}
