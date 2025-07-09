#!/usr/bin/env python3
"""
🚀 БЫСТРЫЙ ЗАПУСК НОВОСТНОГО БОТА
Все настроено! Просто запустите: python start.py
"""

import subprocess
import sys
import os

def print_header():
    """Красивый заголовок"""
    print("="*60)
    print("🤖 НОВОСТНОЙ ТЕЛЕГРАМ БОТ С ИИ")
    print("🚀 Автоматический запуск")
    print("="*60)
    print()

def check_python():
    """Проверка версии Python"""
    print("🐍 Проверяем Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Нужна версия 3.8+")
        return False

def install_requirements():
    """Установка зависимостей"""
    print("\n📦 Устанавливаем зависимости...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def test_system():
    """Тестирование системы"""
    print("\n🔍 Тестируем систему...")
    try:
        result = subprocess.run([sys.executable, "main.py", "test"], 
                               capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Система готова к работе")
            return True
        else:
            print(f"❌ Ошибка тестирования: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Тестирование заняло слишком много времени")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def run_bot():
    """Запуск бота"""
    print("\n🤖 Запускаем бота...")
    print("⚠️  Для остановки нажмите Ctrl+C")
    print("-"*60)
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен пользователем")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка запуска бота: {e}")

def main():
    """Главная функция"""
    print_header()
    
    # Проверяем Python
    if not check_python():
        print("\n🚨 Обновите Python до версии 3.8 или выше")
        return
    
    # Устанавливаем зависимости
    if not install_requirements():
        print("\n🚨 Не удалось установить зависимости")
        return
    
    # Тестируем систему
    if not test_system():
        print("\n⚠️  Система не прошла тестирование, но попробуем запустить...")
    
    # Запускаем бота
    run_bot()
    
    print("\n👋 До свидания!")

if __name__ == "__main__":
    main()