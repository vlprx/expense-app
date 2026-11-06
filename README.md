# Expense App


## Використані технології

- Python 3.13
- Flask 3.1.3
- Docker
- Docker Compose
- GitHub Actions
- Ruff

## Структура проєкту

```text
expense-app/
├── app/
│   ├── __init__.py
│   └── views.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── run.py
└── README.md
```

## Вимоги до середовища

Перед запуском застосунку необхідно встановити:

- Docker Desktop
- Git

Перед початком роботи переконайтеся, що Docker Desktop запущений.

## Запуск за допомогою Docker Compose

Клонуйте репозиторій:

```bash
git clone https://github.com/vlprx/expense-app.git
cd expense-app
```

Зберіть Docker-образ і запустіть застосунок:

```bash
docker compose up --build -d
```

Перевірте стан запущених контейнерів:

```bash
docker compose ps
```

Після запуску застосунок буде доступний за адресами:

- Перевірка життєздатності (Liveness): http://localhost:5000/healthz/live
- Перевірка готовності (Readiness): http://localhost:5000/healthz/ready

## API перевірки стану застосунку (Health Check API)

### GET /healthz/live

Перевіряє, чи працює процес застосунку.

Приклад відповіді:

```json
{
  "status": "alive",
  "timestamp": "2026-11-06T00:00:00+00:00"
}
```

### GET /healthz/ready

Перевіряє готовність застосунку до обробки запитів.

Приклад відповіді:

```json
{
  "status": "ready",
  "database": "not_connected_yet",
  "timestamp": "2026-11-06T00:00:00+00:00"
}
```

## Зупинка застосунку

Для зупинки та видалення контейнерів виконайте команду:

```bash
docker compose down
```

## Автоматизація перевірок (CI Pipeline)

GitHub Actions автоматично запускає перевірки після кожного надсилання змін (`push`) або створення запиту на злиття (`pull_request`) у гілки `main` та `master`.

CI-пайплайн виконує такі етапи:

1. Встановлення необхідних залежностей.
2. Статичний аналіз коду за допомогою Ruff.
3. Збирання Docker-образу.
4. Перевірка коректності конфігурації Docker Compose.

## Керування залежностями

Усі залежності Python та їхні версії зафіксовані у файлі `requirements.txt`.