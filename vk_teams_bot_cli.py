#!/usr/bin/env python3
"""
VK Teams Bot CLI Utility

Простая CLI утилита для управления VK Teams ботом.
"""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("❌ Требуется httpx: pip install httpx")
    sys.exit(1)


class VKTeamsBotCLI:
    """CLI для управления VK Teams ботом"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
    
    async def configure_bot(self, token: str, api_url: str, auto_start: bool = True) -> Dict[str, Any]:
        """Настройка бота"""
        try:
            payload = {
                "bot_token": token,
                "api_url": api_url,
                "auto_start": auto_start
            }
            
            response = await self.client.post(
                "/api/v1/vk-teams/bot/configure",
                json=payload,
                headers={"Authorization": "Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Бот успешно настроен!")
                print(f"Bot ID: {data.get('config', {}).get('bot_id', 'N/A')}")
                return data
            else:
                print(f"❌ Ошибка настройки: {response.status_code}")
                return {"success": False}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса бота"""
        try:
            response = await self.client.get(
                "/api/v1/vk-teams/bot/status",
                headers={"Authorization": "Bearer demo-token"}
            )
            
            if response.status_code == 200:
                data = response.json()
                status = "Активен" if data.get("is_active") else "Неактивен"
                print(f"📊 Статус бота: {status}")
                print(f"Bot ID: {data.get('bot_id', 'N/A')}")
                print(f"Сообщений: {data.get('stats', {}).get('total_messages', 0)}")
                return data
            else:
                print(f"❌ Ошибка получения статуса: {response.status_code}")
                return {"success": False}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_webhook(self) -> Dict[str, Any]:
        """Тестирование webhook"""
        try:
            test_data = {
                "test_event": "message",
                "test_data": {"text": "Test from CLI"}
            }
            
            response = await self.client.post(
                "/api/v1/vk-teams/webhook/test",
                json=test_data
            )
            
            if response.status_code == 200:
                print("✅ Webhook тест прошел успешно!")
                return response.json()
            else:
                print(f"❌ Ошибка тестирования: {response.status_code}")
                return {"success": False}
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"success": False, "error": str(e)}


async def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(description="VK Teams Bot CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # Configure command
    configure_parser = subparsers.add_parser("configure", help="Настроить бота")
    configure_parser.add_argument("--token", required=True, help="Токен бота")
    configure_parser.add_argument("--api-url", required=True, help="URL API")
    
    # Status command
    subparsers.add_parser("status", help="Статус бота")
    
    # Test command
    subparsers.add_parser("test", help="Тест webhook")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = VKTeamsBotCLI()
    
    try:
        if args.command == "configure":
            await cli.configure_bot(args.token, args.api_url)
        elif args.command == "status":
            await cli.get_status()
        elif args.command == "test":
            await cli.test_webhook()
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await cli.client.aclose()


if __name__ == "__main__":
    asyncio.run(main()) 