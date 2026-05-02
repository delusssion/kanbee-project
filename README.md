# KanBee

**Канбан-доска и трекер задач для продуктивной работы**

[![Live Demo](https://img.shields.io/badge/demo-kanbee.ru-E8C050?style=for-the-badge&logo=google-chrome&logoColor=white)](https://kanbee.ru)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Vanilla JS](https://img.shields.io/badge/Vanilla_JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

</div>

---

## О проекте

**KanBee** — лёгкое веб-приложение для управления задачами. Канбан-доска с drag & drop, трекер задач с фильтрацией, поддержка тём и двух языков — всё это без тяжёлых фреймворков на фронтенде.

## Возможности

| Функция | Описание |
|---|---|
| **Канбан-доска** | Три колонки: To Do / In Process / Done |
| **Drag & Drop** | Перетаскивание карточек мышью и тачем (мобильные) |
| **Трекер задач** | Табличный вид с поиском и фильтрами по статусу и приоритету |
| **Приоритеты** | High / Medium / Low с цветовой индикацией |
| **Дедлайны** | Дата выполнения, подсветка просроченных задач |
| **Авторизация** | Регистрация и вход, смена пароля, сессионные куки |
| **Тёмная / светлая тема** | Переключение с сохранением в профиле |
| **Мультиязычность** | Русский и английский интерфейс |
| **Настройки** | Язык, тема и вид по умолчанию сохраняются в БД |

## Стек технологий

**Backend**
- [FastAPI](https://fastapi.tiangolo.com) — веб-фреймворк
- [PostgreSQL](https://postgresql.org) — база данных
- [psycopg2](https://pypi.org/project/psycopg2-binary/) — драйвер PostgreSQL
- [bcrypt](https://pypi.org/project/bcrypt/) — хэширование паролей
- [uvicorn](https://www.uvicorn.org) — ASGI-сервер

**Frontend**
- Vanilla JS, HTML5, CSS3 — без фреймворков и сборщиков
- Google Fonts (Syne, Lora, DM Sans)

**Инфраструктура**
- Nginx — reverse proxy и раздача статики
- Certbot / Let's Encrypt — SSL-сертификат

## Структура проекта

```
kanbee-project/
├── backend/
│   ├── routers/
│   │   ├── auth.py        # Регистрация, вход, смена пароля
│   │   ├── tasks.py       # CRUD задач
│   │   └── settings.py    # Настройки пользователя
│   ├── models/
│   │   ├── user.py
│   │   └── task.py
│   ├── main.py            # FastAPI-приложение, CORS, роуты
│   ├── storage.py         # Работа с PostgreSQL
│   ├── auth_utils.py      # Зависимость get_current_user_id
│   └── requirements.txt
├── css/
│   └── styles.css         # Все стили (тёмная и светлая тема)
├── js/
│   ├── app.js             # Логика доски и трекера
│   └── auth.js            # Логика страницы входа
├── board.html             # Канбан-доска и трекер задач
├── registration.html      # Страница входа / регистрации
└── index.html             # Редирект на board или registration
```

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <repo-url>
cd kanbee-project
```

### 2. Настроить базу данных

```bash
createdb kanbee
```

### 3. Запустить backend

```bash
cd backend
pip install -r requirements.txt

cp .env.example .env
# Отредактировать .env: указать DATABASE_URL

export $(cat .env | xargs)
uvicorn main:app --reload --port 8000
```

### 4. Открыть frontend

Открыть `index.html` в браузере или запустить локальный HTTP-сервер:

```bash
cd ..
python3 -m http.server 3000
# Открыть http://localhost:3000
```

## Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql://user:pass@localhost/kanbee` |

## API

Документация доступна автоматически через FastAPI:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`

### Основные эндпоинты

```
POST   /auth/register        — Регистрация
POST   /auth/login           — Вход
POST   /auth/logout          — Выход
GET    /auth/me              — Текущий пользователь
POST   /auth/change-password — Смена пароля

GET    /tasks                — Список задач
POST   /tasks                — Создать задачу
PATCH  /tasks/{id}           — Обновить задачу
DELETE /tasks/{id}           — Удалить задачу

GET    /settings             — Настройки пользователя
PATCH  /settings             — Обновить настройки
```

## Деплой

Проект задеплоен на VPS с Nginx + systemd:

- Nginx раздаёт статику из `/opt/kanbee/frontend`
- FastAPI работает на `127.0.0.1:8000` под управлением systemd
- Nginx проксирует запросы к `/auth/*`, `/tasks/*`, `/settings/*` на backend
- SSL через Let's Encrypt (Certbot)

---

<div align="center">
  Сделано с ♥ и без лишних зависимостей
</div>
