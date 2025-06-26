#!/usr/bin/env python3
"""
Demo script for WebSocket functionality
Demonstrates connection management, messaging, and notifications
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
import websockets
import requests
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketDemo:
    """Demo class for WebSocket functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000", ws_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.connections: Dict[str, Any] = {}
        
    async def demonstrate_basic_connection(self):
        """Demonstrate basic WebSocket connection"""
        logger.info("=== Демонстрация базового подключения ===")
        
        uri = f"{self.ws_url}/api/v1/ws/demo_user"
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Подключен к {uri}")
                
                # Ожидаем приветственное сообщение
                welcome_msg = await websocket.recv()
                logger.info(f"Получено приветствие: {welcome_msg}")
                
                # Отправляем ping
                ping_msg = {"type": "ping"}
                await websocket.send(json.dumps(ping_msg))
                logger.info(f"Отправлен ping: {ping_msg}")
                
                # Получаем pong
                pong_response = await websocket.recv()
                logger.info(f"Получен pong: {pong_response}")
                
                # Получаем статистику
                stats_msg = {"type": "get_stats"}
                await websocket.send(json.dumps(stats_msg))
                logger.info(f"Запросили статистику: {stats_msg}")
                
                stats_response = await websocket.recv()
                logger.info(f"Получена статистика: {stats_response}")
                
                # Корректное отключение
                disconnect_msg = {"type": "disconnect"}
                await websocket.send(json.dumps(disconnect_msg))
                logger.info("Отправлен запрос на отключение")
                
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
    
    async def demonstrate_multiple_connections(self):
        """Demonstrate multiple concurrent connections"""
        logger.info("=== Демонстрация множественных подключений ===")
        
        users = ["user1", "user2", "user3"]
        tasks = []
        
        async def create_user_connection(user_id: str):
            uri = f"{self.ws_url}/api/v1/ws/{user_id}"
            try:
                async with websockets.connect(uri) as websocket:
                    logger.info(f"Пользователь {user_id} подключен")
                    
                    # Слушаем сообщения в течение 10 секунд
                    end_time = time.time() + 10
                    while time.time() < end_time:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            logger.info(f"{user_id} получил: {message}")
                        except asyncio.TimeoutError:
                            # Отправляем периодический ping
                            await websocket.send(json.dumps({"type": "ping"}))
                        except Exception as e:
                            logger.error(f"Ошибка для {user_id}: {e}")
                            break
                    
                    logger.info(f"Пользователь {user_id} отключается")
            except Exception as e:
                logger.error(f"Ошибка подключения для {user_id}: {e}")
        
        # Создаем подключения для всех пользователей
        for user_id in users:
            tasks.append(create_user_connection(user_id))
        
        # Запускаем все подключения параллельно
        await asyncio.gather(*tasks)
    
    def demonstrate_rest_api(self):
        """Demonstrate REST API for WebSocket management"""
        logger.info("=== Демонстрация REST API ===")
        
        try:
            # Получаем статистику соединений
            response = requests.get(f"{self.base_url}/api/v1/ws/stats")
            logger.info(f"Статистика соединений: {response.json()}")
            
            # Примечание: для отправки уведомлений нужна аутентификация
            # Здесь показан только формат запроса
            notification_example = {
                "notification_type": "demo",
                "message": {
                    "title": "Demo Notification",
                    "content": "This is a demo notification"
                }
            }
            logger.info(f"Пример уведомления: {notification_example}")
            
            broadcast_example = {
                "notification_type": "system",
                "message": {
                    "title": "System Demo",
                    "content": "This is a system broadcast demo"
                }
            }
            logger.info(f"Пример broadcast: {broadcast_example}")
            
        except Exception as e:
            logger.error(f"Ошибка REST API: {e}")
    
    async def demonstrate_message_types(self):
        """Demonstrate different message types"""
        logger.info("=== Демонстрация типов сообщений ===")
        
        uri = f"{self.ws_url}/api/v1/ws/message_demo_user"
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("Подключен для демонстрации сообщений")
                
                # Список сообщений для отправки
                messages = [
                    {"type": "ping"},
                    {"type": "get_stats"},
                    {"type": "custom_message", "content": "Hello WebSocket!"},
                    {"type": "test", "data": {"key": "value"}},
                    {"invalid": "json_without_type"}
                ]
                
                for msg in messages:
                    logger.info(f"Отправляем: {msg}")
                    await websocket.send(json.dumps(msg))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        logger.info(f"Получен ответ: {response}")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout ожидания ответа")
                
                # Ждем heartbeat сообщения
                logger.info("Ожидаем heartbeat сообщения...")
                try:
                    heartbeat = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    logger.info(f"Получен heartbeat: {heartbeat}")
                except asyncio.TimeoutError:
                    logger.info("Heartbeat не получен в течение таймаута")
                
                # Корректное отключение
                await websocket.send(json.dumps({"type": "disconnect"}))
                
        except Exception as e:
            logger.error(f"Ошибка демонстрации сообщений: {e}")
    
    async def demonstrate_error_handling(self):
        """Demonstrate error handling scenarios"""
        logger.info("=== Демонстрация обработки ошибок ===")
        
        uri = f"{self.ws_url}/api/v1/ws/error_demo_user"
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("Подключен для демонстрации ошибок")
                
                # Отправляем невалидный JSON
                logger.info("Отправляем невалидный JSON...")
                await websocket.send("invalid json string")
                
                try:
                    error_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    logger.info(f"Получен ответ на ошибку: {error_response}")
                except asyncio.TimeoutError:
                    logger.warning("Не получен ответ на невалидный JSON")
                
                # Отправляем сообщение с неизвестным типом
                unknown_msg = {"type": "unknown_command", "data": "test"}
                logger.info(f"Отправляем неизвестную команду: {unknown_msg}")
                await websocket.send(json.dumps(unknown_msg))
                
                echo_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Получен echo ответ: {echo_response}")
                
        except Exception as e:
            logger.error(f"Ошибка демонстрации ошибок: {e}")
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        logger.info("🚀 Запуск демонстрации WebSocket функциональности")
        logger.info("Убедитесь, что сервер запущен на localhost:8000")
        
        try:
            # Проверяем доступность сервера
            response = requests.get(f"{self.base_url}/health")
            logger.info(f"Сервер доступен: {response.json()}")
        except Exception as e:
            logger.error(f"Сервер недоступен: {e}")
            return
        
        # Запускаем демонстрации
        demos = [
            ("Базовое подключение", self.demonstrate_basic_connection()),
            ("Типы сообщений", self.demonstrate_message_types()),
            ("Обработка ошибок", self.demonstrate_error_handling()),
            ("REST API", None),  # Синхронная функция
            ("Множественные подключения", self.demonstrate_multiple_connections()),
        ]
        
        for name, demo_task in demos:
            logger.info(f"\n{'='*50}")
            logger.info(f"Запуск: {name}")
            logger.info(f"{'='*50}")
            
            if demo_task is None:
                # Синхронная функция
                self.demonstrate_rest_api()
            else:
                try:
                    await demo_task
                except Exception as e:
                    logger.error(f"Ошибка в демо '{name}': {e}")
            
            # Пауза между демонстрациями
            await asyncio.sleep(2)
        
        logger.info("\n🎉 Демонстрация завершена!")


async def main():
    """Main function to run WebSocket demos"""
    demo = WebSocketDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    print("""
    WebSocket Demo Script
    =====================
    
    Этот скрипт демонстрирует возможности WebSocket функциональности:
    
    1. Базовое подключение и ping-pong
    2. Различные типы сообщений
    3. Обработка ошибок
    4. REST API для управления
    5. Множественные подключения
    
    Для запуска убедитесь, что:
    1. Сервер запущен: uvicorn app.main:app --reload
    2. Установлены зависимости: pip install websockets requests
    
    Нажмите Ctrl+C для остановки.
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}") 