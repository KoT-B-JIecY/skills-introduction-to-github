# 📰 News Bot - Телеграм бот для парсинга новостей с ИИ

Мощный телеграм-бот для автоматического парсинга новостей с различных источников, обработки их с помощью ИИ (Claude, GigaChat, OpenAI) и публикации в телеграм канале.

## 🌟 Возможности

- 🔄 **Автоматический парсинг** новостей из RSS лент и HTML страниц
- 🤖 **ИИ обработка** новостей (Claude, GigaChat, OpenAI)
- 📝 **Редактирование новостей**: заголовки, содержание, категории, эмодзи
- 📊 **Многофункциональная админ панель** с множеством команд
- ⏰ **Планировщик задач** для автоматизации
- 🗄️ **База данных** для хранения новостей и статистики
- 📱 **Telegram интеграция** для управления и публикации
- 🔍 **Проверка дубликатов** новостей
- 📈 **Детальная статистика** и логирование

## 🚀 Быстрый старт

### 1. Установка

```bash
# Клонируйте репозиторий
git clone <your-repository-url>
cd news_bot

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
# Скопируйте файл примера настроек
cp .env.example .env

# Откройте .env в текстовом редакторе и заполните настройки
nano .env
```

### 3. Настройка Telegram

#### Создание бота:
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Используйте команду `/newbot`
3. Следуйте инструкциям и получите токен бота
4. Добавьте токен в `.env` как `TELEGRAM_BOT_TOKEN`

#### Создание канала:
1. Создайте новый канал в Telegram
2. Добавьте вашего бота как администратора канала
3. Получите ID канала (начинается с @ или -100...)
4. Добавьте ID в `.env` как `TELEGRAM_CHANNEL_ID`

#### Получение вашего ID:
1. Напишите [@userinfobot](https://t.me/userinfobot)
2. Получите ваш ID
3. Добавьте ID в `.env` как `ADMIN_USER_ID`

### 4. Настройка ИИ провайдеров

#### Claude (Anthropic) - РЕКОМЕНДУЕТСЯ:
1. Зарегистрируйтесь на [console.anthropic.com](https://console.anthropic.com/)
2. Создайте API ключ
3. Добавьте ключ в `.env` как `CLAUDE_API_KEY`

#### GigaChat (Сбер):
1. Зарегистрируйтесь на [developers.sber.ru](https://developers.sber.ru/portal/products/gigachat)
2. Получите credentials
3. Добавьте в `.env` как `GIGACHAT_CLIENT_ID` и `GIGACHAT_CLIENT_SECRET`

#### OpenAI (опционально):
1. Получите API ключ на [platform.openai.com](https://platform.openai.com/)
2. Добавьте ключ в `.env` как `OPENAI_API_KEY`

### 5. Запуск

```bash
# Запуск бота
python main.py

# Или разовый парсинг для тестирования
python main.py parse

# Или тестирование настроек
python main.py test
```

## ⚙️ Настройка

### Файл .env

```env
# ========== ТЕЛЕГРАМ ==========
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_name
ADMIN_USER_ID=123456789

# ========== ИИ ИНТЕГРАЦИЯ ==========
CLAUDE_API_KEY=your_claude_api_key_here
GIGACHAT_CLIENT_ID=your_gigachat_client_id
GIGACHAT_CLIENT_SECRET=your_gigachat_client_secret
OPENAI_API_KEY=your_openai_key_here

# ========== ПАРСИНГ ==========
PARSING_INTERVAL=30
MAX_NEWS_PER_BATCH=5
USE_AI_PROCESSING=true
AUTO_PUBLISH=false
```

### Источники новостей

Настройте источники в файле `config/settings.py`:

```python
NEWS_SOURCES = [
    {
        "name": "РБК RSS",
        "url": "https://rbc.ru/rss/news",
        "type": "rss",
        "enabled": True,
        "category": "Общие новости"
    },
    {
        "name": "Habr HTML",
        "url": "https://habr.com/ru/news/",
        "type": "html",
        "enabled": True,
        "category": "Технологии",
        "parsing_config": {
            "news_list": ".tm-articles-list article",
            "title": ".tm-article-snippet__title-link",
            "content": ".tm-article-snippet__lead"
        }
    }
]
```

## 🎮 Команды администратора

После запуска бота, используйте эти команды в личных сообщениях с ботом:

### 📰 Управление новостями:
- `/start_parsing` - Запустить парсинг
- `/stop_parsing` - Остановить парсинг
- `/manual_parse` - Ручной парсинг
- `/pending_news` - Показать неопубликованные новости
- `/publish_news [id]` - Опубликовать новость
- `/delete_news [id]` - Удалить новость

### ⚙️ Настройки:
- `/settings` - Показать настройки
- `/sources` - Управление источниками
- `/add_source` - Добавить источник
- `/remove_source [id]` - Удалить источник
- `/categories` - Управление категориями

### 📊 Статистика:
- `/stats` - Общая статистика
- `/logs` - Показать логи
- `/status` - Статус системы

### 🤖 ИИ управление:
- `/ai_settings` - Настройки ИИ
- `/test_ai` - Тестировать ИИ
- `/reprocess_news [id]` - Переобработать новость ИИ

### 🔄 Планировщик:
- `/scheduler_status` - Статус планировщика
- `/set_interval [минуты]` - Установить интервал парсинга

## 📁 Структура проекта

```
news_bot/
├── main.py                 # Главный файл запуска
├── requirements.txt        # Зависимости
├── .env.example           # Пример настроек
├── README.md              # Документация
├── config/
│   └── settings.py        # Основные настройки
├── database/
│   ├── models.py          # Модели базы данных
│   └── database.py        # Работа с БД
├── parsers/
│   ├── base_parser.py     # Базовый парсер
│   ├── rss_parser.py      # RSS парсер
│   ├── html_parser.py     # HTML парсер
│   └── parser_manager.py  # Менеджер парсеров
├── ai_integration/
│   └── ai_processor.py    # ИИ обработка
├── bot/
│   ├── handlers.py        # Обработчики команд
│   ├── admin.py           # Админ панель
│   └── publisher.py       # Публикация новостей
├── scheduler/
│   └── task_scheduler.py  # Планировщик задач
└── utils/
    └── logger.py          # Логирование
```

## 🔧 Добавление новых источников

### RSS источник:
```python
{
    "name": "Название источника",
    "url": "https://example.com/rss",
    "type": "rss",
    "enabled": True,
    "category": "Категория"
}
```

### HTML источник:
```python
{
    "name": "Название сайта",
    "url": "https://example.com/news",
    "type": "html",
    "enabled": True,
    "category": "Категория",
    "parsing_config": {
        "news_list": ".news-item",           # Список новостей
        "title": ".news-title",              # Заголовок
        "content": ".news-content",          # Содержание
        "link": ".news-link",                # Ссылка
        "image": ".news-image img",          # Изображение
        "author": ".news-author",            # Автор
        "date": ".news-date"                 # Дата
    }
}
```

### HTML с Selenium (для динамических сайтов):
```python
{
    "name": "SPA сайт",
    "url": "https://spa-example.com",
    "type": "html",
    "enabled": True,
    "category": "Технологии",
    "use_selenium": True,
    "parsing_config": {
        # Те же селекторы что и для HTML
    }
}
```

## 🤖 Настройка ИИ промптов

В файле `config/settings.py` можно настроить промпты для ИИ:

```python
class AIPrompts:
    NEWS_PROCESSING = """
    Ты - редактор новостей. Обработай новость для публикации:
    
    1. Создай привлекательный заголовок (до 100 символов)
    2. Перепиши новость кратко и понятно (до 1000 символов)
    3. Добавь подходящие эмодзи
    4. Определи категорию
    5. Сохрани фактическую точность
    
    Исходная новость:
    Заголовок: {title}
    Текст: {content}
    Источник: {source}
    
    Ответь в формате JSON:
    {{
        "title": "обработанный заголовок",
        "content": "обработанный текст",
        "category": "категория",
        "emoji": "основной эмодзи"
    }}
    """
```

## 📊 База данных

Бот автоматически создает SQLite базу данных со следующими таблицами:

- **news** - Новости
- **news_sources** - Источники новостей
- **users** - Пользователи
- **bot_settings** - Настройки бота
- **parsed_urls** - Отслеживание дубликатов
- **ai_processing_logs** - Логи ИИ обработки

## 🚨 Устранение проблем

### Бот не запускается:
1. Проверьте токен бота в `.env`
2. Убедитесь что все зависимости установлены
3. Проверьте логи в папке `logs/`

### Парсинг не работает:
1. Тестируйте источники: `python main.py test`
2. Проверьте доступность сайтов
3. Обновите селекторы для HTML парсеров

### ИИ не обрабатывает новости:
1. Проверьте API ключи
2. Проверьте баланс на ИИ сервисах
3. Тестируйте провайдеры: `/test_ai`

### Новости не публикуются:
1. Проверьте права бота в канале
2. Убедитесь что бот добавлен как администратор
3. Проверьте ID канала

## 📝 Логирование

Все логи сохраняются в папке `logs/`:
- `bot.log` - Основные логи
- `errors.log` - Только ошибки

Уровень логирования настраивается в `.env`:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## 🔄 Автоматизация

### Systemd сервис (Linux):
```ini
[Unit]
Description=News Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/news_bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## UC Shop Telegram-бот (aiogram)

### Запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Укажите токен бота и строку подключения к PostgreSQL в переменных окружения:
   ```bash
   export UC_BOT_TOKEN=your_bot_token
   export UC_POSTGRES_DSN=postgresql://user:pass@localhost:5432/ucshop
   ```
3. Запустите бота:
   ```bash
   python bot/telegram_bot.py
   ```

### Функционал
- Главное меню: Купить UC, Цены, Профиль, Поддержка, Акции
- Быстрый выбор номинала UC (60/300/600/1800)
- FSM для сценария покупки
- Мультиязычность (ru/en/ar)
- Подключение к PostgreSQL (шаблон)

Дальнейшее расширение: интеграция платежей, рефералы, промокоды, турниры, уведомления и т.д.

## 🤝 Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте логи в папке `logs/`
2. Используйте команду `python main.py test` для диагностики
3. Проверьте настройки в `.env`

## 📄 Лицензия

MIT License - вы можете свободно использовать и модифицировать код.

---

**🎉 Поздравляем! Ваш бот готов к работе. Теперь вы можете наслаждаться автоматическим парсингом и публикацией новостей с ИИ обработкой!**

