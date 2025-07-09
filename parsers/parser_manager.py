import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from parsers.base_parser import BaseParser, NewsItem
from parsers.rss_parser import RSSParser
from parsers.html_parser import HTMLParser
from database.database import (
    db_manager, NewsService, SourceService, 
    get_url_hash
)
from database.models import News, NewsSource, ParsedURL, NewsStatus
from ai_integration.ai_processor import ai_manager
from config.settings import settings
from utils.logger import logger, PerformanceLogger, log_parsing_result


class ParserFactory:
    """Фабрика для создания парсеров"""
    
    @staticmethod
    def create_parser(source_config: Dict[str, Any]) -> Optional[BaseParser]:
        """
        Создание парсера на основе конфигурации
        
        Args:
            source_config: Конфигурация источника
            
        Returns:
            Экземпляр парсера или None
        """
        source_type = source_config.get("type", "").lower()
        
        try:
            if source_type == "rss":
                return RSSParser(source_config)
            elif source_type == "html":
                return HTMLParser(source_config)
            else:
                logger.error(f"Неизвестный тип источника: {source_type}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка создания парсера {source_type}: {e}")
            return None


class DuplicateChecker:
    """Класс для проверки дубликатов новостей"""
    
    def __init__(self):
        self.recent_hashes = set()
        self.last_cleanup = datetime.utcnow()
    
    def is_duplicate(self, news_item: NewsItem, session) -> bool:
        """
        Проверка является ли новость дубликатом
        
        Args:
            news_item: Объект новости
            session: Сессия базы данных
            
        Returns:
            True если новость является дубликатом
        """
        # Проверяем в кэше
        if news_item.hash in self.recent_hashes:
            return True
        
        # Проверяем в базе данных по URL
        if news_item.url:
            url_hash = get_url_hash(news_item.url)
            existing_url = session.query(ParsedURL).filter(
                ParsedURL.url_hash == url_hash
            ).first()
            
            if existing_url:
                return True
        
        # Проверяем по хешу контента
        existing_news = session.query(News).filter(
            News.title == news_item.title
        ).first()
        
        if existing_news:
            # Дополнительная проверка по содержанию
            content_snippet = news_item.content[:100]
            existing_snippet = existing_news.content[:100]
            
            if content_snippet == existing_snippet:
                return True
        
        # Добавляем в кэш
        self.recent_hashes.add(news_item.hash)
        
        # Очищаем кэш если прошло много времени
        if datetime.utcnow() - self.last_cleanup > timedelta(hours=1):
            self._cleanup_cache()
        
        return False
    
    def _cleanup_cache(self):
        """Очистка кэша старых хешей"""
        self.recent_hashes.clear()
        self.last_cleanup = datetime.utcnow()
        logger.debug("Кэш дубликатов очищен")


class NewsProcessor:
    """Класс для обработки новостей"""
    
    def __init__(self):
        self.duplicate_checker = DuplicateChecker()
    
    def process_news_items(self, news_items: List[NewsItem], 
                          source_id: int) -> Tuple[int, int, int]:
        """
        Обработка списка новостей
        
        Args:
            news_items: Список новостей
            source_id: ID источника
            
        Returns:
            Кортеж (создано, дубликатов, ошибок)
        """
        created_count = 0
        duplicate_count = 0
        error_count = 0
        
        with db_manager.get_session() as session:
            for news_item in news_items:
                try:
                    # Проверяем на дубликаты
                    if self.duplicate_checker.is_duplicate(news_item, session):
                        duplicate_count += 1
                        logger.debug(f"Дубликат новости: {news_item.title[:50]}...")
                        continue
                    
                    # Создаем запись в базе данных
                    news_data = {
                        "title": news_item.title,
                        "content": news_item.content,
                        "url": news_item.url,
                        "author": news_item.author,
                        "image_url": news_item.image_url,
                        "category": news_item.category,
                        "tags": news_item.tags,
                        "source_id": source_id,
                        "status": NewsStatus.PENDING.value,
                        "parsed_at": news_item.published_at
                    }
                    
                    # Создаем новость
                    news = NewsService.create_news(session, news_data)
                    
                    # Сохраняем URL для проверки дубликатов
                    if news_item.url:
                        url_hash = get_url_hash(news_item.url)
                        parsed_url = ParsedURL(
                            url=news_item.url,
                            url_hash=url_hash,
                            news_id=news.id,
                            source_id=source_id
                        )
                        session.add(parsed_url)
                    
                    # Запускаем обработку ИИ если включена
                    if settings.USE_AI_PROCESSING:
                        self._process_with_ai(news, session)
                    
                    created_count += 1
                    logger.info(f"Создана новость {news.id}: {news_item.title[:50]}...")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Ошибка обработки новости: {e}")
                    session.rollback()
                    continue
            
            # Сохраняем изменения
            session.commit()
        
        return created_count, duplicate_count, error_count
    
    def _process_with_ai(self, news: News, session):
        """Обработка новости с помощью ИИ"""
        try:
            source_name = news.source.name if news.source else "Unknown"
            
            # Обрабатываем новость ИИ
            success, result, provider = ai_manager.process_news_with_ai(
                news.id, news.title, news.content, source_name
            )
            
            if success:
                # Обновляем новость обработанными данными
                news.processed_title = result.get("title", news.title)
                news.processed_content = result.get("content", news.content)
                news.category = result.get("category", news.category)
                news.emoji = result.get("emoji", "")
                news.status = NewsStatus.PROCESSED.value
                
                logger.info(f"Новость {news.id} обработана ИИ [{provider}]")
                
                # Если включена автопубликация, публикуем
                if settings.AUTO_PUBLISH:
                    news.status = NewsStatus.PUBLISHED.value
                    news.published_at = datetime.utcnow()
            else:
                news.ai_processing_attempts += 1
                news.ai_processing_error = "Ошибка обработки ИИ"
                logger.error(f"Ошибка ИИ обработки новости {news.id}")
                
        except Exception as e:
            logger.error(f"Ошибка ИИ обработки: {e}")


class ParserManager:
    """Главный менеджер парсеров"""
    
    def __init__(self):
        self.news_processor = NewsProcessor()
        self.is_parsing = False
        self.last_parsing_time = None
        self.parsing_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "total_news_found": 0,
            "total_news_created": 0,
            "total_duplicates": 0,
            "total_errors": 0
        }
        
        logger.info("Менеджер парсеров инициализирован")
    
    def get_active_sources(self) -> List[NewsSource]:
        """Получение активных источников новостей"""
        with db_manager.get_session() as session:
            return SourceService.get_active_sources(session)
    
    def parse_single_source(self, source: NewsSource) -> Dict[str, Any]:
        """
        Парсинг одного источника
        
        Args:
            source: Источник новостей
            
        Returns:
            Метрики парсинга
        """
        try:
            logger.info(f"Начинаем парсинг источника: {source.name}")
            
            # Конфигурация источника
            source_config = {
                "name": source.name,
                "url": source.url,
                "type": source.source_type,
                "category": source.category,
                "enabled": source.enabled,
                "parsing_config": source.parsing_config or {}
            }
            
            # Создаем парсер
            parser = ParserFactory.create_parser(source_config)
            if not parser:
                return {
                    "source_id": source.id,
                    "source_name": source.name,
                    "success": False,
                    "error": "Не удалось создать парсер",
                    "news_found": 0,
                    "news_created": 0,
                    "duplicates": 0,
                    "processing_time": 0
                }
            
            try:
                # Парсим новости
                news_items, parsing_metrics = parser.parse_with_metrics()
                
                if not parsing_metrics["success"]:
                    return {
                        "source_id": source.id,
                        "source_name": source.name,
                        "success": False,
                        "error": parsing_metrics["error"],
                        "news_found": 0,
                        "news_created": 0,
                        "duplicates": 0,
                        "processing_time": parsing_metrics["processing_time"]
                    }
                
                # Обрабатываем новости
                created, duplicates, errors = self.news_processor.process_news_items(
                    news_items, source.id
                )
                
                # Обновляем статистику источника
                with db_manager.get_session() as session:
                    SourceService.update_source_stats(
                        session, source.id, success=True
                    )
                    
                    # Обновляем общую статистику источника
                    source_obj = session.query(NewsSource).filter(
                        NewsSource.id == source.id
                    ).first()
                    if source_obj:
                        source_obj.total_news_count += len(news_items)
                        source_obj.success_count += created
                        session.commit()
                
                metrics = {
                    "source_id": source.id,
                    "source_name": source.name,
                    "success": True,
                    "error": None,
                    "news_found": len(news_items),
                    "news_created": created,
                    "duplicates": duplicates,
                    "errors": errors,
                    "processing_time": parsing_metrics["processing_time"]
                }
                
                log_parsing_result(
                    source.name, created, errors, 
                    parsing_metrics["processing_time"]
                )
                
                return metrics
                
            finally:
                # Закрываем парсер
                parser.close()
                
        except Exception as e:
            # Обновляем статистику ошибок
            with db_manager.get_session() as session:
                SourceService.update_source_stats(
                    session, source.id, success=False
                )
            
            logger.error(f"Ошибка парсинга источника {source.name}: {e}")
            
            return {
                "source_id": source.id,
                "source_name": source.name,
                "success": False,
                "error": str(e),
                "news_found": 0,
                "news_created": 0,
                "duplicates": 0,
                "processing_time": 0
            }
    
    def parse_all_sources(self, max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        Парсинг всех активных источников
        
        Args:
            max_workers: Максимальное количество потоков
            
        Returns:
            Список метрик для каждого источника
        """
        if self.is_parsing:
            logger.warning("Парсинг уже выполняется")
            return []
        
        self.is_parsing = True
        
        try:
            with PerformanceLogger("Parsing all sources"):
                sources = self.get_active_sources()
                
                if not sources:
                    logger.warning("Нет активных источников для парсинга")
                    return []
                
                logger.info(f"Начинаем парсинг {len(sources)} источников")
                
                all_metrics = []
                
                # Используем ThreadPoolExecutor для параллельного парсинга
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Запускаем парсинг всех источников
                    future_to_source = {
                        executor.submit(self.parse_single_source, source): source
                        for source in sources
                    }
                    
                    # Собираем результаты
                    for future in as_completed(future_to_source):
                        source = future_to_source[future]
                        
                        try:
                            metrics = future.result()
                            all_metrics.append(metrics)
                            
                        except Exception as e:
                            logger.error(f"Ошибка получения результата парсинга {source.name}: {e}")
                            all_metrics.append({
                                "source_id": source.id,
                                "source_name": source.name,
                                "success": False,
                                "error": str(e),
                                "news_found": 0,
                                "news_created": 0,
                                "duplicates": 0,
                                "processing_time": 0
                            })
                
                # Обновляем общую статистику
                self._update_parsing_stats(all_metrics)
                self.last_parsing_time = datetime.utcnow()
                
                # Логируем общие результаты
                total_found = sum(m["news_found"] for m in all_metrics)
                total_created = sum(m["news_created"] for m in all_metrics)
                total_duplicates = sum(m["duplicates"] for m in all_metrics)
                successful_sources = sum(1 for m in all_metrics if m["success"])
                
                logger.info(
                    f"Парсинг завершен: {successful_sources}/{len(sources)} источников, "
                    f"найдено {total_found}, создано {total_created}, дубликатов {total_duplicates}"
                )
                
                return all_metrics
                
        finally:
            self.is_parsing = False
    
    def _update_parsing_stats(self, metrics_list: List[Dict[str, Any]]):
        """Обновление статистики парсинга"""
        self.parsing_stats["total_runs"] += 1
        
        successful_runs = sum(1 for m in metrics_list if m["success"])
        if successful_runs > 0:
            self.parsing_stats["successful_runs"] += 1
        
        self.parsing_stats["total_news_found"] += sum(m["news_found"] for m in metrics_list)
        self.parsing_stats["total_news_created"] += sum(m["news_created"] for m in metrics_list)
        self.parsing_stats["total_duplicates"] += sum(m["duplicates"] for m in metrics_list)
        
        error_runs = sum(1 for m in metrics_list if not m["success"])
        self.parsing_stats["total_errors"] += error_runs
    
    def get_parsing_status(self) -> Dict[str, Any]:
        """Получение статуса парсинга"""
        return {
            "is_parsing": self.is_parsing,
            "last_parsing_time": self.last_parsing_time,
            "stats": self.parsing_stats.copy()
        }
    
    def test_source(self, source_id: int) -> Dict[str, Any]:
        """
        Тестирование одного источника
        
        Args:
            source_id: ID источника
            
        Returns:
            Результат тестирования
        """
        with db_manager.get_session() as session:
            source = session.query(NewsSource).filter(
                NewsSource.id == source_id
            ).first()
            
            if not source:
                return {
                    "success": False,
                    "error": "Источник не найден"
                }
            
            # Отключаем сохранение в БД для тестирования
            original_processor = self.news_processor
            self.news_processor = TestNewsProcessor()
            
            try:
                result = self.parse_single_source(source)
                return result
            finally:
                self.news_processor = original_processor


class TestNewsProcessor(NewsProcessor):
    """Тестовый процессор новостей (не сохраняет в БД)"""
    
    def process_news_items(self, news_items: List[NewsItem], 
                          source_id: int) -> Tuple[int, int, int]:
        """Обработка новостей без сохранения в БД"""
        return len(news_items), 0, 0


# Глобальный экземпляр менеджера парсеров
parser_manager = ParserManager()