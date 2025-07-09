#!/usr/bin/env python3
"""
Телеграм бот для парсинга новостей с ИИ обработкой
Главный файл для запуска всех компонентов системы
"""

import os
import sys
import signal
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.logger import logger
from database.database import init_database
from scheduler.task_scheduler import task_scheduler
from parsers.parser_manager import parser_manager
from ai_integration.ai_processor import ai_manager


class NewsBot:
    """Главный класс телеграм бота для новостей"""
    
    def __init__(self):
        """Инициализация бота"""
        self.is_running = False
        self.components_initialized = False
        
        # Устанавливаем обработчики сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("📰 News Bot инициализируется...")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Получен сигнал {signum}, начинаем остановку...")
        self.stop()
        sys.exit(0)
    
    def initialize_components(self):
        """Инициализация всех компонентов системы"""
        try:
            logger.info("🔧 Инициализация компонентов...")
            
            # 1. Проверяем настройки
            self._validate_settings()
            
            # 2. Инициализируем базу данных
            logger.info("💾 Инициализация базы данных...")
            init_database()
            
            # 3. Проверяем ИИ провайдеры
            logger.info("🤖 Проверка ИИ провайдеров...")
            self._check_ai_providers()
            
            # 4. Инициализируем планировщик
            logger.info("⏰ Инициализация планировщика...")
            task_scheduler.start()
            
            self.components_initialized = True
            logger.info("✅ Все компоненты инициализированы успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    def _validate_settings(self):
        """Проверка основных настроек"""
        logger.info("🔍 Проверка настроек...")
        
        # Проверяем обязательные настройки
        required_settings = [
            ("TELEGRAM_BOT_TOKEN", "Токен телеграм бота"),
            ("TELEGRAM_CHANNEL_ID", "ID телеграм канала"),
            ("ADMIN_USER_ID", "ID администратора")
        ]
        
        missing_settings = []
        
        for setting_name, description in required_settings:
            value = getattr(settings, setting_name, None)
            if not value or str(value) in ["YOUR_BOT_TOKEN_HERE", "@your_channel_name", "0"]:
                missing_settings.append(f"{setting_name} ({description})")
        
        if missing_settings:
            logger.error("❌ Не заполнены обязательные настройки:")
            for setting in missing_settings:
                logger.error(f"   - {setting}")
            logger.error("📝 Пожалуйста, заполните файл .env или config/settings.py")
            raise ValueError("Не заполнены обязательные настройки")
        
        # Проверяем источники новостей
        if not settings.NEWS_SOURCES:
            logger.warning("⚠️ Не настроены источники новостей")
        else:
            enabled_sources = [s for s in settings.NEWS_SOURCES if s.get("enabled", True)]
            logger.info(f"📡 Настроено {len(enabled_sources)} активных источников новостей")
        
        logger.info("✅ Настройки проверены")
    
    def _check_ai_providers(self):
        """Проверка ИИ провайдеров"""
        provider_status = ai_manager.get_provider_status()
        
        available_providers = [name for name, available in provider_status.items() if available]
        
        if available_providers:
            logger.info(f"🤖 Доступные ИИ провайдеры: {', '.join(available_providers)}")
        else:
            logger.warning("⚠️ Ни один ИИ провайдер не настроен или недоступен")
            logger.warning("   Новости будут парситься без ИИ обработки")
    
    def start(self):
        """Запуск бота"""
        if self.is_running:
            logger.warning("⚠️ Бот уже запущен")
            return
        
        try:
            logger.info("🚀 Запуск News Bot...")
            
            # Инициализируем компоненты если еще не сделали
            if not self.components_initialized:
                self.initialize_components()
            
            self.is_running = True
            
            # Выводим информацию о статусе
            self._print_status()
            
            # Основной цикл работы
            self._run_main_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки от пользователя")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            self.stop()
            raise
    
    def _run_main_loop(self):
        """Основной цикл работы"""
        logger.info("🔄 Запуск основного цикла...")
        
        try:
            # Запускаем первый парсинг вручную
            logger.info("📰 Запускаем первоначальный парсинг...")
            self.manual_parse()
            
            # Основной цикл - просто держим процесс живым
            logger.info("✅ Бот запущен и работает. Для остановки нажмите Ctrl+C")
            
            while self.is_running:
                try:
                    # Проверяем статус каждые 30 секунд
                    import time
                    time.sleep(30)
                    
                    # Здесь можно добавить периодические проверки
                    self._periodic_health_check()
                    
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            logger.error(f"❌ Ошибка в основном цикле: {e}")
            raise
    
    def _periodic_health_check(self):
        """Периодическая проверка состояния системы"""
        try:
            # Проверяем планировщик
            if not task_scheduler.is_running:
                logger.warning("⚠️ Планировщик не запущен, перезапускаем...")
                task_scheduler.start()
            
            # Можно добавить другие проверки
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки состояния: {e}")
    
    def stop(self):
        """Остановка бота"""
        if not self.is_running:
            return
        
        logger.info("🛑 Остановка News Bot...")
        
        try:
            # Останавливаем планировщик
            if task_scheduler.is_running:
                logger.info("⏰ Остановка планировщика...")
                task_scheduler.stop()
            
            # Закрываем подключение к БД
            logger.info("💾 Закрытие подключения к базе данных...")
            from database.database import db_manager
            db_manager.close_engine()
            
            self.is_running = False
            logger.info("✅ News Bot остановлен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки: {e}")
    
    def manual_parse(self):
        """Ручной запуск парсинга"""
        logger.info("🔄 Запуск ручного парсинга...")
        
        try:
            results = parser_manager.parse_all_sources()
            
            # Выводим результаты
            total_found = sum(r.get("news_found", 0) for r in results)
            total_created = sum(r.get("news_created", 0) for r in results)
            total_duplicates = sum(r.get("duplicates", 0) for r in results)
            successful_sources = sum(1 for r in results if r.get("success", False))
            
            logger.info(
                f"📊 Результаты парсинга: "
                f"{successful_sources}/{len(results)} источников, "
                f"найдено {total_found}, создано {total_created}, дубликатов {total_duplicates}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка ручного парсинга: {e}")
            return []
    
    def _print_status(self):
        """Вывод статуса системы"""
        logger.info("=" * 60)
        logger.info("📰 NEWS BOT STATUS")
        logger.info("=" * 60)
        
        # Статус компонентов
        logger.info(f"🗂️  База данных: {'✅ Подключена' if self.components_initialized else '❌ Ошибка'}")
        logger.info(f"⏰ Планировщик: {'✅ Запущен' if task_scheduler.is_running else '❌ Остановлен'}")
        
        # ИИ провайдеры
        provider_status = ai_manager.get_provider_status()
        available_providers = [name for name, available in provider_status.items() if available]
        logger.info(f"🤖 ИИ провайдеры: {'✅ ' + ', '.join(available_providers) if available_providers else '❌ Недоступны'}")
        
        # Источники новостей
        active_sources = len([s for s in settings.NEWS_SOURCES if s.get("enabled", True)])
        logger.info(f"📡 Источники: ✅ {active_sources} активных")
        
        # Настройки
        logger.info(f"🔄 Интервал парсинга: {settings.PARSING_INTERVAL} минут")
        logger.info(f"🤖 ИИ обработка: {'✅ Включена' if settings.USE_AI_PROCESSING else '❌ Отключена'}")
        logger.info(f"📢 Автопубликация: {'✅ Включена' if settings.AUTO_PUBLISH else '❌ Отключена'}")
        
        logger.info("=" * 60)
    
    def get_status(self):
        """Получение статуса в виде словаря"""
        return {
            "is_running": self.is_running,
            "components_initialized": self.components_initialized,
            "scheduler_status": task_scheduler.get_status(),
            "parser_status": parser_manager.get_parsing_status(),
            "ai_providers": ai_manager.get_provider_status()
        }


def print_help():
    """Вывод справки по использованию"""
    help_text = """
📰 News Bot - Telegram бот для парсинга и публикации новостей

ИСПОЛЬЗОВАНИЕ:
    python main.py [КОМАНДА]

КОМАНДЫ:
    start           Запустить бота (по умолчанию)
    parse           Выполнить разовый парсинг
    test            Тестировать настройки и компоненты
    status          Показать статус системы
    help            Показать эту справку

ПРИМЕРЫ:
    python main.py              # Запуск бота
    python main.py parse        # Разовый парсинг
    python main.py test         # Тестирование
    python main.py status       # Статус системы

📝 НАСТРОЙКА:
    1. Скопируйте .env.example в .env
    2. Заполните все необходимые токены и настройки
    3. Настройте источники новостей в config/settings.py
    4. Запустите: python main.py

🔗 ДОКУМЕНТАЦИЯ:
    Подробная документация в файле README.md
    """
    print(help_text)


def main():
    """Главная функция"""
    # Получаем команду из аргументов
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "help" or command == "--help" or command == "-h":
        print_help()
        return
    
    # Создаем экземпляр бота
    bot = NewsBot()
    
    try:
        if command == "start":
            # Обычный запуск бота
            bot.start()
            
        elif command == "parse":
            # Разовый парсинг
            print("🔄 Выполняем разовый парсинг...")
            bot.initialize_components()
            results = bot.manual_parse()
            
            # Выводим детальные результаты
            print("\n📊 РЕЗУЛЬТАТЫ ПАРСИНГА:")
            print("-" * 50)
            for result in results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['source_name']}: "
                      f"найдено {result['news_found']}, "
                      f"создано {result['news_created']}")
                
                if not result["success"] and result.get("error"):
                    print(f"   Ошибка: {result['error']}")
            
        elif command == "test":
            # Тестирование компонентов
            print("🧪 Тестируем компоненты системы...")
            
            try:
                bot.initialize_components()
                print("✅ Все компоненты инициализированы успешно")
                
                # Тестируем ИИ провайдеры
                print("\n🤖 Тестируем ИИ провайдеры...")
                for provider_name in ["claude", "gigachat", "openai"]:
                    success, message = ai_manager.test_provider(provider_name)
                    status = "✅" if success else "❌"
                    print(f"{status} {provider_name}: {message}")
                
                print("\n✅ Тестирование завершено")
                
            except Exception as e:
                print(f"❌ Ошибка тестирования: {e}")
                sys.exit(1)
            
        elif command == "status":
            # Показать статус
            print("📊 Получаем статус системы...")
            bot.initialize_components()
            bot._print_status()
            
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("Используйте 'python main.py help' для справки")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Остановка по запросу пользователя")
        bot.stop()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        bot.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()