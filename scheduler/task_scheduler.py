import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from parsers.parser_manager import parser_manager
from database.database import db_manager, BotSettings
from config.settings import settings
from utils.logger import logger, PerformanceLogger


class TaskScheduler:
    """Планировщик задач для автоматического парсинга"""
    
    def __init__(self):
        """Инициализация планировщика"""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.jobs = {}
        
        # Статистика
        self.stats = {
            "total_jobs_executed": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "last_execution": None,
            "last_error": None,
            "uptime_start": datetime.utcnow()
        }
        
        # Настройка слушателей событий
        self.scheduler.add_listener(
            self._job_executed_listener, 
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        logger.info("Планировщик задач инициализирован")
    
    def start(self):
        """Запуск планировщика"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        try:
            self.scheduler.start()
            self.is_running = True
            
            # Добавляем задачи по умолчанию
            self._setup_default_jobs()
            
            logger.info("Планировщик задач запущен")
            
        except Exception as e:
            logger.error(f"Ошибка запуска планировщика: {e}")
            raise
    
    def stop(self):
        """Остановка планировщика"""
        if not self.is_running:
            logger.warning("Планировщик не запущен")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Планировщик задач остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка остановки планировщика: {e}")
    
    def _setup_default_jobs(self):
        """Настройка задач по умолчанию"""
        try:
            # Основная задача парсинга
            self.add_parsing_job(
                interval_minutes=settings.PARSING_INTERVAL,
                job_id="main_parsing"
            )
            
            # Задача очистки старых логов (раз в день)
            self.add_cleanup_job(
                hour=2,  # Выполнять в 2 ночи
                minute=0,
                job_id="daily_cleanup"
            )
            
            # Задача обновления статистики (каждый час)
            self.add_stats_update_job(
                interval_minutes=60,
                job_id="stats_update"
            )
            
            logger.info("Задачи по умолчанию настроены")
            
        except Exception as e:
            logger.error(f"Ошибка настройки задач по умолчанию: {e}")
    
    def add_parsing_job(self, interval_minutes: int, job_id: str = "parsing_job") -> bool:
        """
        Добавление задачи парсинга
        
        Args:
            interval_minutes: Интервал выполнения в минутах
            job_id: Идентификатор задачи
            
        Returns:
            True если задача добавлена успешно
        """
        try:
            # Удаляем существующую задачу если есть
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            # Добавляем новую задачу
            job = self.scheduler.add_job(
                func=self._parsing_job_wrapper,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id=job_id,
                name=f"Парсинг новостей (каждые {interval_minutes} мин)",
                max_instances=1,  # Только одна задача одновременно
                coalesce=True,    # Объединяем пропущенные запуски
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                "job": job,
                "type": "parsing",
                "interval_minutes": interval_minutes,
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"Добавлена задача парсинга: {job_id} (интервал: {interval_minutes} мин)")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления задачи парсинга: {e}")
            return False
    
    def add_cleanup_job(self, hour: int, minute: int, job_id: str = "cleanup_job") -> bool:
        """
        Добавление задачи очистки
        
        Args:
            hour: Час выполнения (0-23)
            minute: Минута выполнения (0-59)
            job_id: Идентификатор задачи
            
        Returns:
            True если задача добавлена успешно
        """
        try:
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            job = self.scheduler.add_job(
                func=self._cleanup_job_wrapper,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=job_id,
                name=f"Очистка данных ({hour:02d}:{minute:02d})",
                max_instances=1,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                "job": job,
                "type": "cleanup",
                "schedule": f"{hour:02d}:{minute:02d}",
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"Добавлена задача очистки: {job_id} (время: {hour:02d}:{minute:02d})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления задачи очистки: {e}")
            return False
    
    def add_stats_update_job(self, interval_minutes: int, job_id: str = "stats_job") -> bool:
        """
        Добавление задачи обновления статистики
        
        Args:
            interval_minutes: Интервал выполнения в минутах
            job_id: Идентификатор задачи
            
        Returns:
            True если задача добавлена успешно
        """
        try:
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            job = self.scheduler.add_job(
                func=self._stats_update_job_wrapper,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id=job_id,
                name=f"Обновление статистики (каждые {interval_minutes} мин)",
                max_instances=1,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                "job": job,
                "type": "stats",
                "interval_minutes": interval_minutes,
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"Добавлена задача статистики: {job_id} (интервал: {interval_minutes} мин)")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления задачи статистики: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """
        Удаление задачи
        
        Args:
            job_id: Идентификатор задачи
            
        Returns:
            True если задача удалена успешно
        """
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"Задача {job_id} удалена")
                return True
            else:
                logger.warning(f"Задача {job_id} не найдена")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """Приостановка задачи"""
        try:
            if job_id in self.jobs:
                self.scheduler.pause_job(job_id)
                logger.info(f"Задача {job_id} приостановлена")
                return True
            else:
                logger.warning(f"Задача {job_id} не найдена")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка приостановки задачи {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Возобновление задачи"""
        try:
            if job_id in self.jobs:
                self.scheduler.resume_job(job_id)
                logger.info(f"Задача {job_id} возобновлена")
                return True
            else:
                logger.warning(f"Задача {job_id} не найдена")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка возобновления задачи {job_id}: {e}")
            return False
    
    def _parsing_job_wrapper(self):
        """Обертка для задачи парсинга"""
        try:
            with PerformanceLogger("Scheduled parsing job"):
                logger.info("Запуск автоматического парсинга")
                
                # Проверяем настройки
                if not self._is_parsing_enabled():
                    logger.info("Автоматический парсинг отключен в настройках")
                    return
                
                # Выполняем парсинг
                results = parser_manager.parse_all_sources()
                
                # Логируем результаты
                total_created = sum(r.get("news_created", 0) for r in results)
                total_found = sum(r.get("news_found", 0) for r in results)
                successful_sources = sum(1 for r in results if r.get("success", False))
                
                logger.info(
                    f"Автоматический парсинг завершен: "
                    f"{successful_sources} источников, "
                    f"найдено {total_found}, создано {total_created}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка в задаче парсинга: {e}")
            raise
    
    def _cleanup_job_wrapper(self):
        """Обертка для задачи очистки"""
        try:
            with PerformanceLogger("Cleanup job"):
                logger.info("Запуск задачи очистки")
                
                # Очистка старых новостей (старше 30 дней)
                self._cleanup_old_news(days=30)
                
                # Очистка старых логов ИИ (старше 7 дней)
                self._cleanup_ai_logs(days=7)
                
                # Очистка старых URL (старше 60 дней)
                self._cleanup_old_urls(days=60)
                
                logger.info("Задача очистки завершена")
                
        except Exception as e:
            logger.error(f"Ошибка в задаче очистки: {e}")
            raise
    
    def _stats_update_job_wrapper(self):
        """Обертка для задачи обновления статистики"""
        try:
            logger.debug("Обновление статистики")
            
            # Здесь можно добавить обновление различных метрик
            # Например, подсчет активных пользователей, статистика по источникам и т.д.
            
        except Exception as e:
            logger.error(f"Ошибка в задаче статистики: {e}")
            raise
    
    def _is_parsing_enabled(self) -> bool:
        """Проверка включен ли автоматический парсинг"""
        try:
            with db_manager.get_session() as session:
                setting = session.query(BotSettings).filter(
                    BotSettings.key == "parsing_enabled"
                ).first()
                
                if setting:
                    return setting.value.lower() == "true"
                
                # По умолчанию включен
                return True
                
        except Exception as e:
            logger.error(f"Ошибка проверки настроек парсинга: {e}")
            return True
    
    def _cleanup_old_news(self, days: int):
        """Очистка старых новостей"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with db_manager.get_session() as session:
                from database.models import News
                
                # Удаляем только отклоненные или опубликованные новости
                deleted_count = session.query(News).filter(
                    News.created_at < cutoff_date,
                    News.status.in_(["published", "rejected"])
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Удалено {deleted_count} старых новостей")
                    
        except Exception as e:
            logger.error(f"Ошибка очистки старых новостей: {e}")
    
    def _cleanup_ai_logs(self, days: int):
        """Очистка старых логов ИИ"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with db_manager.get_session() as session:
                from database.models import AIProcessingLog
                
                deleted_count = session.query(AIProcessingLog).filter(
                    AIProcessingLog.created_at < cutoff_date
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Удалено {deleted_count} старых логов ИИ")
                    
        except Exception as e:
            logger.error(f"Ошибка очистки логов ИИ: {e}")
    
    def _cleanup_old_urls(self, days: int):
        """Очистка старых URL"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with db_manager.get_session() as session:
                from database.models import ParsedURL
                
                deleted_count = session.query(ParsedURL).filter(
                    ParsedURL.created_at < cutoff_date
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Удалено {deleted_count} старых URL")
                    
        except Exception as e:
            logger.error(f"Ошибка очистки старых URL: {e}")
    
    def _job_executed_listener(self, event):
        """Слушатель событий выполнения задач"""
        try:
            self.stats["total_jobs_executed"] += 1
            self.stats["last_execution"] = datetime.utcnow()
            
            if event.exception:
                self.stats["failed_jobs"] += 1
                self.stats["last_error"] = str(event.exception)
                logger.error(f"Ошибка выполнения задачи {event.job_id}: {event.exception}")
            else:
                self.stats["successful_jobs"] += 1
                logger.debug(f"Задача {event.job_id} выполнена успешно")
                
        except Exception as e:
            logger.error(f"Ошибка в слушателе событий: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса планировщика"""
        jobs_info = []
        
        for job_id, job_info in self.jobs.items():
            job = job_info["job"]
            
            jobs_info.append({
                "id": job_id,
                "name": job.name,
                "type": job_info["type"],
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "created_at": job_info["created_at"].isoformat()
            })
        
        return {
            "is_running": self.is_running,
            "jobs_count": len(self.jobs),
            "jobs": jobs_info,
            "stats": self.stats.copy(),
            "uptime": (datetime.utcnow() - self.stats["uptime_start"]).total_seconds()
        }
    
    def update_parsing_interval(self, new_interval_minutes: int) -> bool:
        """
        Обновление интервала парсинга
        
        Args:
            new_interval_minutes: Новый интервал в минутах
            
        Returns:
            True если обновлено успешно
        """
        try:
            # Сохраняем новый интервал в настройках
            with db_manager.get_session() as session:
                setting = session.query(BotSettings).filter(
                    BotSettings.key == "parsing_interval"
                ).first()
                
                if setting:
                    setting.value = str(new_interval_minutes)
                else:
                    setting = BotSettings(
                        key="parsing_interval",
                        value=str(new_interval_minutes),
                        description="Интервал парсинга в минутах"
                    )
                    session.add(setting)
                
                session.commit()
            
            # Обновляем задачу парсинга
            return self.add_parsing_job(new_interval_minutes, "main_parsing")
            
        except Exception as e:
            logger.error(f"Ошибка обновления интервала парсинга: {e}")
            return False


# Глобальный экземпляр планировщика
task_scheduler = TaskScheduler()