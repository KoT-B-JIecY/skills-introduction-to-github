import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

import openai
import anthropic
import requests
from gigachat import GigaChat

from config.settings import settings, AIPrompts
from utils.logger import logger, log_ai_processing, PerformanceLogger


class AIProvider(ABC):
    """Абстрактный класс для провайдеров ИИ"""
    
    @abstractmethod
    def process_news(self, title: str, content: str, source: str) -> Dict[str, Any]:
        """Обработка новости с помощью ИИ"""
        pass
    
    @abstractmethod
    def categorize_news(self, text: str) -> str:
        """Определение категории новости"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности провайдера"""
        pass


class ClaudeProvider(AIProvider):
    """Провайдер Claude (Anthropic)"""
    
    def __init__(self):
        """Инициализация провайдера Claude"""
        self.client = None
        if settings.CLAUDE_API_KEY and settings.CLAUDE_API_KEY != "your_claude_api_key_here":
            try:
                self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
                logger.info("Claude AI провайдер инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации Claude: {e}")
    
    def is_available(self) -> bool:
        """Проверка доступности Claude"""
        return self.client is not None
    
    def process_news(self, title: str, content: str, source: str) -> Dict[str, Any]:
        """Обработка новости с помощью Claude"""
        if not self.is_available():
            raise Exception("Claude провайдер недоступен")
        
        try:
            # Формируем промпт
            prompt = AIPrompts.NEWS_PROCESSING.format(
                title=title,
                content=content,
                source=source
            )
            
            start_time = time.time()
            
            # Отправляем запрос к Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Используем быструю версию
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            processing_time = time.time() - start_time
            
            # Парсим ответ
            response_text = response.content[0].text
            result = json.loads(response_text)
            
            # Добавляем метаданные
            result.update({
                "processing_time": processing_time,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "provider": "claude"
            })
            
            logger.info(f"Claude обработал новость за {processing_time:.2f}s")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа Claude: {e}")
            raise Exception(f"Ошибка парсинга ответа: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки новости Claude: {e}")
            raise
    
    def categorize_news(self, text: str) -> str:
        """Определение категории новости с помощью Claude"""
        if not self.is_available():
            raise Exception("Claude провайдер недоступен")
        
        try:
            categories = list(settings.CATEGORIES.keys())
            prompt = AIPrompts.CATEGORIZATION.format(
                categories=", ".join(categories),
                text=text
            )
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            category = response.content[0].text.strip()
            
            # Проверяем, что категория существует
            if category in settings.CATEGORIES:
                return category
            else:
                return "Общие новости"
                
        except Exception as e:
            logger.error(f"Ошибка категоризации Claude: {e}")
            return "Общие новости"


class GigaChatProvider(AIProvider):
    """Провайдер GigaChat (Сбер)"""
    
    def __init__(self):
        """Инициализация провайдера GigaChat"""
        self.client = None
        if (settings.GIGACHAT_CLIENT_ID and 
            settings.GIGACHAT_CLIENT_ID != "your_gigachat_client_id"):
            try:
                self.client = GigaChat(
                    credentials=settings.GIGACHAT_CLIENT_ID,
                    scope="GIGACHAT_API_PERS",
                    verify_ssl_certs=False
                )
                logger.info("GigaChat провайдер инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации GigaChat: {e}")
    
    def is_available(self) -> bool:
        """Проверка доступности GigaChat"""
        return self.client is not None
    
    def process_news(self, title: str, content: str, source: str) -> Dict[str, Any]:
        """Обработка новости с помощью GigaChat"""
        if not self.is_available():
            raise Exception("GigaChat провайдер недоступен")
        
        try:
            prompt = AIPrompts.NEWS_PROCESSING.format(
                title=title,
                content=content,
                source=source
            )
            
            start_time = time.time()
            
            response = self.client.chat([
                {
                    "role": "user",
                    "content": prompt
                }
            ])
            
            processing_time = time.time() - start_time
            
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            result.update({
                "processing_time": processing_time,
                "provider": "gigachat"
            })
            
            logger.info(f"GigaChat обработал новость за {processing_time:.2f}s")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа GigaChat: {e}")
            raise Exception(f"Ошибка парсинга ответа: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки новости GigaChat: {e}")
            raise
    
    def categorize_news(self, text: str) -> str:
        """Определение категории новости с помощью GigaChat"""
        if not self.is_available():
            raise Exception("GigaChat провайдер недоступен")
        
        try:
            categories = list(settings.CATEGORIES.keys())
            prompt = AIPrompts.CATEGORIZATION.format(
                categories=", ".join(categories),
                text=text
            )
            
            response = self.client.chat([
                {
                    "role": "user",
                    "content": prompt
                }
            ])
            
            category = response.choices[0].message.content.strip()
            
            if category in settings.CATEGORIES:
                return category
            else:
                return "Общие новости"
                
        except Exception as e:
            logger.error(f"Ошибка категоризации GigaChat: {e}")
            return "Общие новости"


class DeepSeekProvider(AIProvider):
    """Провайдер DeepSeek (основной)"""
    
    def __init__(self):
        """Инициализация провайдера DeepSeek"""
        self.client = None
        if settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY != "":
            try:
                self.client = openai.OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com"
                )
                logger.info("DeepSeek провайдер инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации DeepSeek: {e}")
    
    def is_available(self) -> bool:
        """Проверка доступности DeepSeek"""
        return self.client is not None
    
    def process_news(self, title: str, content: str, source: str) -> Dict[str, Any]:
        """Обработка новости с помощью DeepSeek"""
        if not self.is_available():
            raise Exception("DeepSeek провайдер недоступен")
        
        try:
            prompt = AIPrompts.NEWS_PROCESSING.format(
                title=title,
                content=content,
                source=source
            )
            
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            processing_time = time.time() - start_time
            
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            result.update({
                "processing_time": processing_time,
                "tokens_used": response.usage.total_tokens,
                "provider": "deepseek"
            })
            
            logger.info(f"DeepSeek обработал новость за {processing_time:.2f}s")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа DeepSeek: {e}")
            raise Exception(f"Ошибка парсинга ответа: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки новости DeepSeek: {e}")
            raise
    
    def categorize_news(self, text: str) -> str:
        """Определение категории новости с помощью DeepSeek"""
        if not self.is_available():
            raise Exception("DeepSeek провайдер недоступен")
        
        try:
            categories = list(settings.CATEGORIES.keys())
            prompt = AIPrompts.CATEGORIZATION.format(
                categories=", ".join(categories),
                text=text
            )
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            category = response.choices[0].message.content.strip()
            
            if category in settings.CATEGORIES:
                return category
            else:
                return "Общие новости"
                
        except Exception as e:
            logger.error(f"Ошибка категоризации DeepSeek: {e}")
            return "Общие новости"


class OpenAIProvider(AIProvider):
    """Провайдер OpenAI (резервный)"""
    
    def __init__(self):
        """Инициализация провайдера OpenAI"""
        self.client = None
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "":
            try:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI провайдер инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации OpenAI: {e}")
    
    def is_available(self) -> bool:
        """Проверка доступности OpenAI"""
        return self.client is not None
    
    def process_news(self, title: str, content: str, source: str) -> Dict[str, Any]:
        """Обработка новости с помощью OpenAI"""
        if not self.is_available():
            raise Exception("OpenAI провайдер недоступен")
        
        try:
            prompt = AIPrompts.NEWS_PROCESSING.format(
                title=title,
                content=content,
                source=source
            )
            
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            processing_time = time.time() - start_time
            
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            result.update({
                "processing_time": processing_time,
                "tokens_used": response.usage.total_tokens,
                "provider": "openai"
            })
            
            logger.info(f"OpenAI обработал новость за {processing_time:.2f}s")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа OpenAI: {e}")
            raise Exception(f"Ошибка парсинга ответа: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки новости OpenAI: {e}")
            raise
    
    def categorize_news(self, text: str) -> str:
        """Определение категории новости с помощью OpenAI"""
        if not self.is_available():
            raise Exception("OpenAI провайдер недоступен")
        
        try:
            categories = list(settings.CATEGORIES.keys())
            prompt = AIPrompts.CATEGORIZATION.format(
                categories=", ".join(categories),
                text=text
            )
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            category = response.choices[0].message.content.strip()
            
            if category in settings.CATEGORIES:
                return category
            else:
                return "Общие новости"
                
        except Exception as e:
            logger.error(f"Ошибка категоризации OpenAI: {e}")
            return "Общие новости"


class AIManager:
    """Менеджер для работы с ИИ провайдерами"""
    
    def __init__(self):
        """Инициализация менеджера ИИ"""
        self.providers = {
            "deepseek": DeepSeekProvider(),
            "claude": ClaudeProvider(),
            "gigachat": GigaChatProvider(),
            "openai": OpenAIProvider()
        }
        
        # Определяем порядок приоритета провайдеров (DeepSeek первый!)
        self.priority_order = ["deepseek", "claude", "gigachat", "openai"]
        
        # Находим доступные провайдеры
        self.available_providers = [
            name for name in self.priority_order 
            if self.providers[name].is_available()
        ]
        
        if not self.available_providers:
            logger.warning("Ни один ИИ провайдер не доступен!")
        else:
            logger.info(f"Доступные ИИ провайдеры: {', '.join(self.available_providers)}")
    
    def get_primary_provider(self) -> Optional[AIProvider]:
        """Получение основного провайдера"""
        if self.available_providers:
            provider_name = self.available_providers[0]
            return self.providers[provider_name]
        return None
    
    def process_news_with_ai(self, news_id: int, title: str, content: str, 
                           source: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Обработка новости с помощью ИИ
        
        Возвращает: (успех, результат, провайдер)
        """
        if not settings.USE_AI_PROCESSING:
            logger.info("ИИ обработка отключена в настройках")
            return False, {}, ""
        
        # Пробуем провайдеры по порядку приоритета
        for provider_name in self.available_providers:
            provider = self.providers[provider_name]
            
            try:
                with PerformanceLogger(f"AI processing with {provider_name}"):
                    result = provider.process_news(title, content, source)
                
                # Валидация результата
                if self._validate_ai_result(result):
                    log_ai_processing(
                        news_id, provider_name, True, 
                        result.get("processing_time")
                    )
                    return True, result, provider_name
                else:
                    logger.warning(f"Некорректный результат от {provider_name}")
                    
            except Exception as e:
                log_ai_processing(news_id, provider_name, False, error=str(e))
                logger.warning(f"Ошибка обработки с {provider_name}: {e}")
                continue
        
        # Если все провайдеры не сработали
        logger.error(f"Не удалось обработать новость {news_id} ни одним провайдером")
        return False, {}, ""
    
    def _validate_ai_result(self, result: Dict[str, Any]) -> bool:
        """Валидация результата ИИ обработки"""
        required_fields = ["title", "content", "category"]
        
        for field in required_fields:
            if field not in result or not result[field]:
                return False
        
        # Проверяем категорию
        if result["category"] not in settings.CATEGORIES:
            result["category"] = "Общие новости"
        
        # Проверяем длину заголовка и контента
        if len(result["title"]) > settings.MAX_TITLE_LENGTH:
            result["title"] = result["title"][:settings.MAX_TITLE_LENGTH] + "..."
        
        if len(result["content"]) > settings.MAX_CONTENT_LENGTH:
            result["content"] = result["content"][:settings.MAX_CONTENT_LENGTH] + "..."
        
        return True
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Получение статуса всех провайдеров"""
        return {
            name: provider.is_available() 
            for name, provider in self.providers.items()
        }
    
    def test_provider(self, provider_name: str) -> Tuple[bool, str]:
        """Тестирование конкретного провайдера"""
        if provider_name not in self.providers:
            return False, f"Провайдер {provider_name} не найден"
        
        provider = self.providers[provider_name]
        
        if not provider.is_available():
            return False, f"Провайдер {provider_name} недоступен"
        
        try:
            # Тестовая обработка
            test_title = "Тестовая новость"
            test_content = "Это тестовая новость для проверки работы ИИ"
            test_source = "Тест"
            
            result = provider.process_news(test_title, test_content, test_source)
            
            if self._validate_ai_result(result):
                return True, f"Провайдер {provider_name} работает корректно"
            else:
                return False, f"Провайдер {provider_name} вернул некорректный результат"
                
        except Exception as e:
            return False, f"Ошибка тестирования {provider_name}: {e}"


# Глобальный экземпляр менеджера ИИ
ai_manager = AIManager()