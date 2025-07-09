from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from parsers.base_parser import BaseParser, NewsItem
from utils.logger import logger


class HTMLParser(BaseParser):
    """Парсер для HTML страниц новостных сайтов"""
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        
        # Селекторы для парсинга
        self.selectors = source_config.get("parsing_config", {})
        
        # Использовать ли Selenium для динамических сайтов
        self.use_selenium = source_config.get("use_selenium", False)
        
        # Настройки Selenium
        self.selenium_driver = None
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Настройка Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Запуск без GUI
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.selenium_driver = webdriver.Chrome(options=chrome_options)
            self.selenium_driver.implicitly_wait(10)
            
            logger.info(f"Selenium WebDriver инициализирован для {self.name}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Selenium для {self.name}: {e}")
            self.use_selenium = False
    
    def parse(self) -> List[NewsItem]:
        """Парсинг HTML страницы"""
        try:
            logger.info(f"Начинаем парсинг HTML: {self.url}")
            
            if self.use_selenium and self.selenium_driver:
                return self._parse_with_selenium()
            else:
                return self._parse_with_requests()
                
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML {self.url}: {e}")
            return []
    
    def _parse_with_requests(self) -> List[NewsItem]:
        """Парсинг с использованием requests + BeautifulSoup"""
        response = self._make_request(self.url)
        if not response:
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_news_from_soup(soup)
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML содержимого: {e}")
            return []
    
    def _parse_with_selenium(self) -> List[NewsItem]:
        """Парсинг с использованием Selenium"""
        try:
            self.selenium_driver.get(self.url)
            
            # Ждем загрузки контента
            WebDriverWait(self.selenium_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Получаем HTML и парсим с BeautifulSoup
            html = self.selenium_driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            return self._extract_news_from_soup(soup)
            
        except TimeoutException:
            logger.error(f"Таймаут загрузки страницы: {self.url}")
            return []
        except Exception as e:
            logger.error(f"Ошибка Selenium парсинга: {e}")
            return []
    
    def _extract_news_from_soup(self, soup: BeautifulSoup) -> List[NewsItem]:
        """Извлечение новостей из BeautifulSoup объекта"""
        news_items = []
        
        # Способ 1: Если есть селектор для списка новостей
        if 'news_list' in self.selectors:
            news_items.extend(self._parse_news_list(soup))
        
        # Способ 2: Если есть селекторы для отдельных элементов
        elif 'title' in self.selectors and 'content' in self.selectors:
            news_items.extend(self._parse_individual_elements(soup))
        
        # Способ 3: Автоматическое определение новостных блоков
        else:
            news_items.extend(self._parse_auto_detect(soup))
        
        return news_items
    
    def _parse_news_list(self, soup: BeautifulSoup) -> List[NewsItem]:
        """Парсинг списка новостей"""
        news_items = []
        news_list_selector = self.selectors.get('news_list')
        
        try:
            news_elements = soup.select(news_list_selector)
            
            for element in news_elements:
                news_item = self._extract_news_from_element(element, soup)
                if news_item:
                    news_items.append(news_item)
                    
        except Exception as e:
            logger.error(f"Ошибка парсинга списка новостей: {e}")
        
        return news_items
    
    def _parse_individual_elements(self, soup: BeautifulSoup) -> List[NewsItem]:
        """Парсинг отдельных элементов страницы"""
        news_items = []
        
        try:
            # Получаем все заголовки
            title_selector = self.selectors.get('title')
            titles = soup.select(title_selector) if title_selector else []
            
            # Получаем весь контент или ищем связанный контент
            content_selector = self.selectors.get('content')
            
            for i, title_element in enumerate(titles):
                title = self._clean_text(title_element.get_text())
                if not title or len(title) < 10:
                    continue
                
                # Ищем связанный контент
                content = self._find_related_content(title_element, content_selector, soup)
                if not content or len(content) < 50:
                    continue
                
                # Извлекаем URL
                url = self._extract_article_url(title_element)
                
                # Извлекаем изображение
                image_url = self._extract_related_image(title_element)
                
                news_item = NewsItem(
                    title=title,
                    content=content,
                    url=url,
                    category=self.category,
                    image_url=image_url
                )
                
                news_items.append(news_item)
                
        except Exception as e:
            logger.error(f"Ошибка парсинга отдельных элементов: {e}")
        
        return news_items
    
    def _parse_auto_detect(self, soup: BeautifulSoup) -> List[NewsItem]:
        """Автоматическое определение новостных блоков"""
        news_items = []
        
        try:
            # Ищем потенциальные новостные блоки
            potential_selectors = [
                'article',
                '.news-item',
                '.article',
                '.post',
                '.story',
                '[class*="news"]',
                '[class*="article"]'
            ]
            
            for selector in potential_selectors:
                elements = soup.select(selector)
                
                for element in elements:
                    news_item = self._extract_news_from_element(element, soup)
                    if news_item and news_item.is_valid():
                        news_items.append(news_item)
                        
                # Если нашли новости, прекращаем поиск
                if news_items:
                    break
                    
        except Exception as e:
            logger.error(f"Ошибка автоматического определения: {e}")
        
        return news_items
    
    def _extract_news_from_element(self, element, soup: BeautifulSoup) -> Optional[NewsItem]:
        """Извлечение новости из HTML элемента"""
        try:
            # Извлекаем заголовок
            title = self._extract_title_from_element(element)
            if not title:
                return None
            
            # Извлекаем контент
            content = self._extract_content_from_element(element)
            if not content:
                return None
            
            # Извлекаем URL
            url = self._extract_article_url(element)
            
            # Извлекаем автора
            author = self._extract_author_from_element(element)
            
            # Извлекаем дату
            published_at = self._extract_date_from_element(element)
            
            # Извлекаем изображение
            image_url = self._extract_image_from_element(element)
            
            return NewsItem(
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                image_url=image_url,
                category=self.category
            )
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения новости из элемента: {e}")
            return None
    
    def _extract_title_from_element(self, element) -> Optional[str]:
        """Извлечение заголовка из элемента"""
        title_selectors = [
            self.selectors.get('title', ''),
            'h1', 'h2', 'h3',
            '.title', '.headline', '.header',
            '[class*="title"]', '[class*="headline"]'
        ]
        
        for selector in title_selectors:
            if not selector:
                continue
                
            title_element = element.select_one(selector)
            if title_element:
                title = self._clean_text(title_element.get_text())
                if title and len(title) >= 10:
                    return title
        
        # Если не нашли в селекторах, пробуем текст самого элемента
        element_text = self._clean_text(element.get_text())
        if element_text and len(element_text.split()) >= 3:
            # Берем первые несколько слов как заголовок
            words = element_text.split()[:15]
            return ' '.join(words)
        
        return None
    
    def _extract_content_from_element(self, element) -> Optional[str]:
        """Извлечение контента из элемента"""
        content_selectors = [
            self.selectors.get('content', ''),
            '.content', '.text', '.description', '.summary',
            '[class*="content"]', '[class*="text"]', '[class*="description"]'
        ]
        
        for selector in content_selectors:
            if not selector:
                continue
                
            content_element = element.select_one(selector)
            if content_element:
                content = self._clean_text(content_element.get_text())
                if content and len(content) >= 50:
                    return content
        
        # Если не нашли отдельный контент, используем весь текст элемента
        full_text = self._clean_text(element.get_text())
        if full_text and len(full_text) >= 50:
            return full_text
        
        return None
    
    def _extract_article_url(self, element) -> Optional[str]:
        """Извлечение URL статьи"""
        # Ищем ссылку в элементе
        link_element = element.find('a')
        if link_element:
            href = link_element.get('href')
            if href:
                # Преобразуем относительную ссылку в абсолютную
                return urljoin(self.url, href)
        
        return None
    
    def _extract_author_from_element(self, element) -> Optional[str]:
        """Извлечение автора из элемента"""
        author_selectors = [
            '.author', '.byline', '.writer',
            '[class*="author"]', '[class*="byline"]'
        ]
        
        for selector in author_selectors:
            author_element = element.select_one(selector)
            if author_element:
                author = self._clean_text(author_element.get_text())
                if author:
                    return author
        
        return None
    
    def _extract_date_from_element(self, element) -> datetime:
        """Извлечение даты из элемента"""
        date_selectors = [
            '.date', '.time', '.published', '.timestamp',
            '[class*="date"]', '[class*="time"]'
        ]
        
        for selector in date_selectors:
            date_element = element.select_one(selector)
            if date_element:
                date_text = self._clean_text(date_element.get_text())
                
                # Пробуем извлечь дату из атрибутов
                for attr in ['datetime', 'data-date', 'data-time']:
                    if date_element.has_attr(attr):
                        date_text = date_element[attr]
                        break
                
                if date_text:
                    parsed_date = self._parse_date_string(date_text)
                    if parsed_date:
                        return parsed_date
        
        return datetime.utcnow()
    
    def _extract_image_from_element(self, element) -> Optional[str]:
        """Извлечение изображения из элемента"""
        img_element = element.find('img')
        if img_element:
            return self._extract_image_url(img_element, self.url)
        
        return None
    
    def _parse_date_string(self, date_string: str) -> Optional[datetime]:
        """Парсинг строки даты"""
        try:
            # Различные форматы даты
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M',
                '%d.%m.%Y',
                '%d/%m/%Y %H:%M',
                '%d/%m/%Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_string.strip(), fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Ошибка парсинга даты {date_string}: {e}")
        
        return None
    
    def close(self):
        """Закрытие ресурсов парсера"""
        super().close()
        
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
                logger.debug(f"Selenium WebDriver закрыт для {self.name}")
            except Exception as e:
                logger.error(f"Ошибка закрытия Selenium: {e}")
    
    def __del__(self):
        """Деструктор"""
        try:
            self.close()
        except:
            pass