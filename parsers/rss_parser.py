import feedparser
from datetime import datetime
from typing import List, Optional
import time
from email.utils import parsedate_to_datetime

from parsers.base_parser import BaseParser, NewsItem
from utils.logger import logger


class RSSParser(BaseParser):
    """Парсер для RSS лент"""
    
    def parse(self) -> List[NewsItem]:
        """Парсинг RSS ленты"""
        try:
            logger.info(f"Начинаем парсинг RSS: {self.url}")
            
            # Парсим RSS ленту
            feed = feedparser.parse(self.url)
            
            if feed.bozo:
                logger.warning(f"RSS лента содержит ошибки: {feed.bozo_exception}")
            
            if not feed.entries:
                logger.warning(f"RSS лента пуста: {self.url}")
                return []
            
            news_items = []
            
            for entry in feed.entries:
                try:
                    news_item = self._parse_entry(entry, feed)
                    if news_item:
                        news_items.append(news_item)
                except Exception as e:
                    logger.error(f"Ошибка парсинга записи RSS: {e}")
                    continue
            
            logger.info(f"RSS парсер {self.name}: обработано {len(news_items)} записей")
            return news_items
            
        except Exception as e:
            logger.error(f"Ошибка парсинга RSS {self.url}: {e}")
            return []
    
    def _parse_entry(self, entry, feed) -> Optional[NewsItem]:
        """Парсинг одной записи RSS"""
        try:
            # Извлекаем заголовок
            title = self._clean_text(entry.get('title', ''))
            if not title:
                return None
            
            # Извлекаем содержание
            content = self._extract_content(entry)
            if not content:
                return None
            
            # Извлекаем URL
            url = entry.get('link', '')
            
            # Извлекаем автора
            author = self._extract_author(entry)
            
            # Извлекаем дату публикации
            published_at = self._extract_published_date(entry)
            
            # Извлекаем изображение
            image_url = self._extract_image_from_entry(entry)
            
            # Извлекаем теги/категории
            tags = self._extract_tags(entry)
            
            # Создаем объект новости
            news_item = NewsItem(
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                image_url=image_url,
                category=self.category,
                tags=tags
            )
            
            return news_item
            
        except Exception as e:
            logger.error(f"Ошибка обработки RSS записи: {e}")
            return None
    
    def _extract_content(self, entry) -> str:
        """Извлечение содержания записи"""
        content = ""
        
        # Пробуем разные поля для содержания
        content_fields = [
            'content',
            'description', 
            'summary',
            'summary_detail'
        ]
        
        for field in content_fields:
            if field in entry:
                field_data = entry[field]
                
                if isinstance(field_data, list) and field_data:
                    # Если это список (например, content)
                    content = field_data[0].get('value', '')
                elif isinstance(field_data, dict):
                    # Если это словарь (например, summary_detail)
                    content = field_data.get('value', '')
                else:
                    # Если это строка
                    content = str(field_data)
                
                if content:
                    break
        
        # Очищаем от HTML тегов и лишних символов
        content = self._clean_html_content(content)
        
        return self._clean_text(content)
    
    def _clean_html_content(self, content: str) -> str:
        """Очистка HTML контента"""
        if not content:
            return ""
        
        try:
            from bs4 import BeautifulSoup
            
            # Парсим HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Удаляем ненужные теги
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            
            # Извлекаем текст
            text = soup.get_text(separator=' ', strip=True)
            
            return text
            
        except ImportError:
            # Если BeautifulSoup не установлена, используем простую очистку
            import re
            content = re.sub(r'<[^>]+>', '', content)
            return content
        except Exception as e:
            logger.debug(f"Ошибка очистки HTML: {e}")
            return content
    
    def _extract_author(self, entry) -> Optional[str]:
        """Извлечение автора записи"""
        author_fields = ['author', 'author_detail', 'dc_creator']
        
        for field in author_fields:
            if field in entry:
                author_data = entry[field]
                
                if isinstance(author_data, dict):
                    author = author_data.get('name', author_data.get('value', ''))
                else:
                    author = str(author_data)
                
                if author:
                    return self._clean_text(author)
        
        return None
    
    def _extract_published_date(self, entry) -> datetime:
        """Извлечение даты публикации"""
        date_fields = ['published', 'updated', 'created']
        
        for field in date_fields:
            if field in entry:
                date_string = entry[field]
                
                try:
                    # Пробуем разные способы парсинга даты
                    
                    # 1. Используем parsedate_to_datetime для RFC 2822
                    try:
                        return parsedate_to_datetime(date_string)
                    except:
                        pass
                    
                    # 2. Используем feedparser.parse для разных форматов
                    if hasattr(entry, f'{field}_parsed') and entry[f'{field}_parsed']:
                        time_struct = entry[f'{field}_parsed']
                        return datetime.fromtimestamp(time.mktime(time_struct))
                    
                    # 3. Пробуем стандартные форматы
                    date_formats = [
                        '%Y-%m-%dT%H:%M:%S%z',
                        '%Y-%m-%dT%H:%M:%SZ',
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d',
                        '%a, %d %b %Y %H:%M:%S %z',
                        '%a, %d %b %Y %H:%M:%S GMT'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            return datetime.strptime(date_string, fmt)
                        except:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Ошибка парсинга даты {date_string}: {e}")
                    continue
        
        # Если не удалось извлечь дату, используем текущую
        return datetime.utcnow()
    
    def _extract_image_from_entry(self, entry) -> Optional[str]:
        """Извлечение изображения из RSS записи"""
        try:
            # Проверяем медиа контент
            if 'media_content' in entry:
                for media in entry.media_content:
                    if media.get('type', '').startswith('image/'):
                        return media.get('url')
            
            # Проверяем enclosure
            if 'enclosures' in entry:
                for enclosure in entry.enclosures:
                    if enclosure.get('type', '').startswith('image/'):
                        return enclosure.get('href')
            
            # Проверяем ссылки
            if 'links' in entry:
                for link in entry.links:
                    if link.get('type', '').startswith('image/'):
                        return link.get('href')
            
            # Ищем изображения в содержании
            content = entry.get('description', '') or entry.get('summary', '')
            if content:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    img_tag = soup.find('img')
                    if img_tag:
                        return img_tag.get('src')
                except:
                    pass
        
        except Exception as e:
            logger.debug(f"Ошибка извлечения изображения из RSS: {e}")
        
        return None
    
    def _extract_tags(self, entry) -> List[str]:
        """Извлечение тегов/категорий"""
        tags = []
        
        try:
            # Проверяем теги
            if 'tags' in entry:
                for tag in entry.tags:
                    if isinstance(tag, dict):
                        tag_name = tag.get('term', tag.get('label', ''))
                    else:
                        tag_name = str(tag)
                    
                    if tag_name:
                        tags.append(self._clean_text(tag_name))
            
            # Проверяем категории
            if 'category' in entry:
                category = entry.category
                if category:
                    tags.append(self._clean_text(category))
        
        except Exception as e:
            logger.debug(f"Ошибка извлечения тегов из RSS: {e}")
        
        return tags[:10]  # Ограничиваем количество тегов