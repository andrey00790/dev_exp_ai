#!/usr/bin/env python3
"""
🤖 CLI интерфейс для AI Assistant
Использование: python3 ai_assistant_cli.py [команда] [опции]
"""

import sys
import json
import requests
import argparse
from typing import Dict, Any, List
import os

class AIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, message: str, context: str = "") -> Dict[str, Any]:
        """Отправка сообщения в чат"""
        try:
            data = {
                "message": message,
                "context": context
            }
            response = self.session.post(f"{self.base_url}/api/v1/chat", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def code_review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Код ревью"""
        try:
            data = {
                "code": code,
                "language": language
            }
            response = self.session.post(f"{self.base_url}/api/v1/code-review", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Поиск в документации"""
        try:
            data = {
                "query": query,
                "limit": limit
            }
            response = self.session.post(f"{self.base_url}/api/v1/search", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_rfc(self, title: str, description: str) -> Dict[str, Any]:
        """Генерация RFC"""
        try:
            data = {
                "title": title,
                "description": description
            }
            response = self.session.post(f"{self.base_url}/api/v1/generate-rfc", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def print_json(data: Dict[str, Any]):
    """Красивый вывод JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def interactive_chat(client: AIClient):
    """Интерактивный чат"""
    print("🤖 AI Assistant - Интерактивный чат")
    print("Введите 'quit' для выхода")
    print("-" * 50)
    
    while True:
        try:
            message = input("Вы: ").strip()
            if message.lower() in ['quit', 'exit', 'q']:
                break
            
            if not message:
                continue
            
            print("🤖 AI: ", end="", flush=True)
            response = client.chat(message)
            
            if "error" in response:
                print(f"❌ Ошибка: {response['error']}")
            else:
                print(response.get("response", "Нет ответа"))
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI Assistant CLI")
    parser.add_argument("--url", default="http://localhost:8000", help="URL сервера")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Формат вывода")
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # Health check
    health_parser = subparsers.add_parser("health", help="Проверка здоровья системы")
    
    # Chat
    chat_parser = subparsers.add_parser("chat", help="Отправить сообщение")
    chat_parser.add_argument("message", help="Сообщение")
    chat_parser.add_argument("--context", default="", help="Контекст")
    
    # Interactive chat
    subparsers.add_parser("interactive", help="Интерактивный чат")
    
    # Code review
    review_parser = subparsers.add_parser("review", help="Код ревью")
    review_parser.add_argument("file", help="Файл с кодом")
    review_parser.add_argument("--language", default="python", help="Язык программирования")
    
    # Search
    search_parser = subparsers.add_parser("search", help="Поиск в документации")
    search_parser.add_argument("query", help="Поисковый запрос")
    search_parser.add_argument("--limit", type=int, default=10, help="Лимит результатов")
    
    # RFC generation
    rfc_parser = subparsers.add_parser("rfc", help="Генерация RFC")
    rfc_parser.add_argument("title", help="Заголовок RFC")
    rfc_parser.add_argument("--description", default="", help="Описание")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = AIClient(args.url)
    
    try:
        if args.command == "health":
            result = client.health_check()
            if args.format == "json":
                print_json(result)
            else:
                if "error" in result:
                    print(f"❌ Ошибка: {result['error']}")
                else:
                    print(f"✅ Система работает: {result.get('status', 'OK')}")
        
        elif args.command == "chat":
            result = client.chat(args.message, args.context)
            if args.format == "json":
                print_json(result)
            else:
                if "error" in result:
                    print(f"❌ Ошибка: {result['error']}")
                else:
                    print(f"🤖 Ответ: {result.get('response', 'Нет ответа')}")
        
        elif args.command == "interactive":
            interactive_chat(client)
        
        elif args.command == "review":
            if not os.path.exists(args.file):
                print(f"❌ Файл не найден: {args.file}")
                return
            
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = client.code_review(code, args.language)
            if args.format == "json":
                print_json(result)
            else:
                if "error" in result:
                    print(f"❌ Ошибка: {result['error']}")
                else:
                    print("🔍 РЕЗУЛЬТАТ КОД РЕВЬЮ:")
                    print(f"Качество: {result.get('quality_score', 'N/A')}")
                    print(f"Проблемы: {result.get('issues', [])}")
                    print(f"Рекомендации: {result.get('recommendations', [])}")
        
        elif args.command == "search":
            result = client.search(args.query, args.limit)
            if args.format == "json":
                print_json(result)
            else:
                if "error" in result:
                    print(f"❌ Ошибка: {result['error']}")
                else:
                    print(f"🔍 Результаты поиска для '{args.query}':")
                    for i, doc in enumerate(result.get('documents', []), 1):
                        print(f"{i}. {doc.get('title', 'Без заголовка')}")
                        print(f"   Релевантность: {doc.get('score', 'N/A')}")
                        print(f"   Содержание: {doc.get('content', '')[:100]}...")
                        print()
        
        elif args.command == "rfc":
            result = client.generate_rfc(args.title, args.description)
            if args.format == "json":
                print_json(result)
            else:
                if "error" in result:
                    print(f"❌ Ошибка: {result['error']}")
                else:
                    print("📄 СГЕНЕРИРОВАННЫЙ RFC:")
                    print(result.get('rfc_content', 'Нет содержимого'))
        
    except KeyboardInterrupt:
        print("\n👋 Операция прервана")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main() 