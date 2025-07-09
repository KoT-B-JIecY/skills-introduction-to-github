from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import requests
from urllib.parse import urljoin, urlparse

from utils.logger import logger, PerformanceLogger


class NewsItem:
    """Класс для представления новости"""
    
    def __init__(self, title: str, content: str, url: str = None, 
                 author: str = None, published_at: datetime = None,
                 image_url: str = None, category: str = None, tags: List[str] = None):
        """
        Инициализация новости
        
        Args:
            title: Заголовок новости
            content: Содержание новости
            url: Ссылка на оригинальную новость
            author: Автор новости
            published_at: Время публикации
            image_url: Ссылка на изображение
            category: Категория новости
            tags: Теги новости
        """
        self.title = title.strip() if title else ""
        self.content = content.strip() if content else ""
        self.url = url
        self.author = author
        self.published_at = published_at or datetime.utcnow()
        self.image_url = image_url
        self.category = category
        self.tags = tags or []
        
        # Создаем хеш для проверки дубликатов
        self.hash = self._create_hash()
    
    def _create_hash(self) -> str:
        """Создание хеша новости для проверки дубликатов"""
        # Используем заголовок и первые 100 символов контента
        content_snippet = self.content[:100] if self.content else ""
        hash_string = f"{self.title}{content_snippet}"
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
    
    def is_valid(self) -> bool:
        """Проверка валидности новости"""
        return bool(self.title and self.content and len(self.title) > 10 and len(self.content) > 50)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "author": self.author,
            "published_at": self.published_at,
            "image_url": self.image_url,
            "category": self.category,
            "tags": self.tags,
            "hash": self.hash
        }
    
    def __repr__(self):
        return f"<NewsItem(title='{self.title[:30]}...', hash='{self.hash[:8]}')>"


class BaseParser(ABC):
    """Базовый класс для всех парсеров"""
    
    def __init__(self, source_config: Dict[str, Any]):
        """
        Инициализация парсера
        
        Args:
            source_config: Конфигурация источника
        """
        self.source_config = source_config
        self.name = source_config.get("name", "Unknown")
        self.url = source_config.get("url", "")
        self.category = source_config.get("category", "Общие новости")
        self.enabled = source_config.get("enabled", True)
        
        # Настройки для HTTP запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Настройки сессии
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Настройки таймаутов
        self.timeout = 30
        
        logger.info(f"Инициализирован парсер: {self.name}")
    
    @abstractmethod
    def parse(self) -> List[NewsItem]:
        """
        Основной метод парсинга
        
        Returns:
            Список новостей
        """
        pass
    
    def _make_request(self, url: str, timeout: int = None) -> Optional[requests.Response]:
        """
        Выполнение HTTP запроса с обработкой ошибок
        
        Args:
            url: URL для запроса
            timeout: Таймаут запроса
            
        Returns:
            Ответ сервера или None при ошибке
        """
        try:
            timeout = timeout or self.timeout
            
            logger.debug(f"Запрос к {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            logger.debug(f"Успешный запрос к {url}, статус: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"Таймаут запроса к {url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Ошибка соединения с {url}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка {e.response.status_code} для {url}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к {url}: {e}")
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Очистка текста от лишних символов
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы строк
        text = ' '.join(text.split())
        
        # Удаляем HTML теги если остались
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем лишние символы
        text = text.replace('\xa0', ' ')  # Неразрывный пробел
        text = text.replace('\u200b', '')  # Нулевой пробел
        
        return text.strip()
    
    def _extract_image_url(self, element, base_url: str = None) -> Optional[str]:
        """
        Извлечение URL изображения
        
        Args:
            element: HTML элемент
            base_url: Базовый URL для относительных ссылок
            
        Returns:
            URL изображения или None
        """
        try:
            # Ищем изображение в разных атрибутах
            img_attrs = ['src', 'data-src', 'data-original', 'data-lazy']
            
            for attr in img_attrs:
                img_url = element.get(attr)
                if img_url:
                    # Преобразуем относительную ссылку в абсолютную
                    if base_url and not img_url.startswith(('http://', 'https://')):
                        img_url = urljoin(base_url, img_url)
                    return img_url
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения изображения: {e}")
        
        return None
    
    def _validate_news_item(self, news_item: NewsItem) -> bool:
        """
        Валидация новости
        
        Args:
            news_item: Объект новости
            
        Returns:
            True если новость валидна
        """
        if not news_item.is_valid():
            logger.debug(f"Новость не прошла базовую валидацию: {news_item.title[:30]}...")
            return False
        
        # Дополнительные проверки
        if len(news_item.title) > 500:
            logger.debug(f"Слишком длинный заголовок: {len(news_item.title)} символов")
            return False
        
        if len(news_item.content) > 10000:
            logger.debug(f"Слишком длинный контент: {len(news_item.content)} символов")
            return False
        
        return True
    
    def parse_with_metrics(self) -> tuple[List[NewsItem], Dict[str, Any]]:
        """
        Парсинг с метриками производительности
        
        Returns:
            Кортеж (список новостей, метрики)
        """
        start_time = datetime.utcnow()
        
        try:
            with PerformanceLogger(f"Parsing {self.name}"):
                news_items = self.parse()
            
            # Фильтруем валидные новости
            valid_news = [item for item in news_items if self._validate_news_item(item)]
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            metrics = {
                "source_name": self.name,
                "total_found": len(news_items),
                "valid_news": len(valid_news),
                "invalid_news": len(news_items) - len(valid_news),
                "processing_time": processing_time,
                "success": True,
                "error": None
            }
            
            logger.info(f"Парсер {self.name}: найдено {len(news_items)}, валидных {len(valid_news)}")
            
            return valid_news, metrics
            
        except Exception as e:
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            metrics = {
                "source_name": self.name,
                "total_found": 0,
                "valid_news": 0,
                "invalid_news": 0,
                "processing_time": processing_time,
                "success": False,
                "error": str(e)
            }
            
            logger.error(f"Ошибка парсинга {self.name}: {e}")
            
            return [], metrics
    
    def close(self):
        """Закрытие сессии парсера"""
        try:
            self.session.close()
            logger.debug(f"Сессия парсера {self.name} закрыта")
        except Exception as e:
            logger.error(f"Ошибка закрытия сессии парсера {self.name}: {e}")
    
    def __del__(self):
        """Деструктор - закрываем сессию"""
        try:
            self.close()
        except:
            pass