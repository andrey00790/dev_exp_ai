#!/usr/bin/env python3
"""
🔍 AI Assistant - Скрипт диагностики окружения разработки

Этот скрипт проверяет все компоненты разработки и выдает детальный отчет
о состоянии системы для разработчиков.

Использование:
    python3 scripts/check_dev_environment.py
    python3 scripts/check_dev_environment.py --fix  # Попытаться исправить проблемы
    python3 scripts/check_dev_environment.py --verbose  # Подробный вывод
"""

import sys
import os
import subprocess
import platform
import json
import urllib.request
import urllib.error
import socket
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class EnvironmentChecker:
    def __init__(self, verbose: bool = False, fix: bool = False):
        self.verbose = verbose
        self.fix = fix
        self.results = []
        self.errors = []
        self.warnings = []
        
    def log(self, message: str, level: str = "INFO"):
        """Логирование с цветами"""
        if level == "SUCCESS":
            print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
        elif level == "ERROR":
            print(f"{Colors.RED}❌ {message}{Colors.RESET}")
            self.errors.append(message)
        elif level == "WARNING":
            print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
            self.warnings.append(message)
        elif level == "INFO":
            print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")
        elif level == "VERBOSE" and self.verbose:
            print(f"{Colors.CYAN}🔍 {message}{Colors.RESET}")
            
    def check_command(self, command: str, expected_text: str = None) -> Tuple[bool, str]:
        """Проверка команды"""
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if expected_text and expected_text not in output:
                    return False, f"Expected '{expected_text}' not found in output"
                return True, output
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, "Command not found"
        except Exception as e:
            return False, str(e)
            
    def check_port(self, host: str, port: int) -> bool:
        """Проверка доступности порта"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
            
    def check_http_endpoint(self, url: str) -> Tuple[bool, str]:
        """Проверка HTTP endpoint"""
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                status = response.getcode()
                if status == 200:
                    return True, "OK"
                else:
                    return False, f"HTTP {status}"
        except urllib.error.URLError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
            
    def check_file_exists(self, filepath: str) -> bool:
        """Проверка существования файла"""
        return Path(filepath).exists()
        
    def check_system_info(self):
        """Проверка информации о системе"""
        self.log(f"{Colors.BOLD}🖥️  СИСТЕМНАЯ ИНФОРМАЦИЯ{Colors.RESET}")
        
        # Операционная система
        os_info = platform.system()
        os_version = platform.release()
        arch = platform.machine()
        self.log(f"ОС: {os_info} {os_version} ({arch})", "INFO")
        
        # Python версия
        python_version = sys.version.split()[0]
        if python_version >= "3.11":
            self.log(f"Python: {python_version}", "SUCCESS")
        elif python_version >= "3.9":
            self.log(f"Python: {python_version} (рекомендуется 3.11+)", "WARNING")
        else:
            self.log(f"Python: {python_version} (требуется 3.11+)", "ERROR")
            
        # Доступная память
        if hasattr(os, 'sysconf'):
            try:
                memory_mb = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**2)
                if memory_mb >= 8192:
                    self.log(f"RAM: {memory_mb:.0f} MB", "SUCCESS")
                elif memory_mb >= 4096:
                    self.log(f"RAM: {memory_mb:.0f} MB (рекомендуется 8GB+)", "WARNING")
                else:
                    self.log(f"RAM: {memory_mb:.0f} MB (недостаточно)", "ERROR")
            except:
                self.log("RAM: Не удалось определить", "WARNING")
                
    def check_required_tools(self):
        """Проверка необходимых инструментов"""
        self.log(f"\n{Colors.BOLD}🛠️  НЕОБХОДИМЫЕ ИНСТРУМЕНТЫ{Colors.RESET}")
        
        tools = [
            ("python3", "Python 3"),
            ("pip", "Python Package Manager"),
            ("git", "Version Control"),
            ("docker", "Docker Container Runtime"),
            ("docker-compose", "Docker Compose"),
            ("node", "Node.js Runtime"),
            ("npm", "Node Package Manager"),
        ]
        
        for command, description in tools:
            success, output = self.check_command(f"{command} --version")
            if success:
                version = output.split('\n')[0]
                self.log(f"{description}: {version}", "SUCCESS")
                self.log(f"  Команда: {command}", "VERBOSE")
            else:
                self.log(f"{description}: НЕ НАЙДЕН", "ERROR")
                if self.fix:
                    self.log(f"  Для установки: см. docs/LOCAL_DEVELOPMENT_GUIDE.md", "INFO")
                    
    def check_project_structure(self):
        """Проверка структуры проекта"""
        self.log(f"\n{Colors.BOLD}📁 СТРУКТУРА ПРОЕКТА{Colors.RESET}")
        
        required_files = [
            "app/main.py",
            "app/__init__.py", 
            "requirements.txt", 
            "docker-compose.yml",
            "frontend/package.json",
            "frontend/src/App.tsx",
            ".env.example",
            "openapi.yaml"
        ]
        
        for file_path in required_files:
            if self.check_file_exists(file_path):
                self.log(f"✓ {file_path}", "SUCCESS")
            else:
                self.log(f"✗ {file_path}", "ERROR")
                
        # Проверка важных директорий
        required_dirs = [
            "app/api/v1",
            "app/models", 
            "app/services",
            "frontend/src/components",
            "tests",
            "docs"
        ]
        
        for dir_path in required_dirs:
            if Path(dir_path).is_dir():
                self.log(f"✓ {dir_path}/", "SUCCESS")
            else:
                self.log(f"✗ {dir_path}/", "ERROR")
                
    def check_python_environment(self):
        """Проверка Python окружения"""
        self.log(f"\n{Colors.BOLD}🐍 PYTHON ОКРУЖЕНИЕ{Colors.RESET}")
        
        # Виртуальное окружение
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.log("Виртуальное окружение: АКТИВНО", "SUCCESS")
            self.log(f"  Путь: {sys.prefix}", "VERBOSE")
        else:
            self.log("Виртуальное окружение: НЕ АКТИВНО", "WARNING")
            if self.fix:
                self.log("  Активируйте: source venv/bin/activate", "INFO")
                
        # Проверка основных зависимостей
        required_packages = [
            ("fastapi", "FastAPI framework"),
            ("uvicorn", "ASGI server"),
            ("sqlalchemy", "ORM"),
            ("psycopg2-binary", "PostgreSQL driver"),
            ("redis", "Redis client"),
            ("qdrant-client", "Qdrant vector database client"),
            ("pytest", "Testing framework"),
        ]
        
        for package, description in required_packages:
            try:
                __import__(package.replace('-', '_'))
                # Получаем версию
                try:
                    import pkg_resources
                    version = pkg_resources.get_distribution(package).version
                    self.log(f"{description}: {version}", "SUCCESS")
                except:
                    self.log(f"{description}: УСТАНОВЛЕН", "SUCCESS")
            except ImportError:
                self.log(f"{description}: НЕ УСТАНОВЛЕН", "ERROR")
                if self.fix:
                    self.log(f"  Установить: pip install {package}", "INFO")
                    
    def check_docker_services(self):
        """Проверка Docker сервисов"""
        self.log(f"\n{Colors.BOLD}🐳 DOCKER СЕРВИСЫ{Colors.RESET}")
        
        # Проверка Docker
        success, output = self.check_command("docker --version")
        if not success:
            self.log("Docker не найден", "ERROR")
            return
            
        # Проверка Docker Compose
        success, output = self.check_command("docker-compose --version")
        if not success:
            self.log("Docker Compose не найден", "ERROR")
            return
            
        # Проверка запущенных контейнеров
        success, output = self.check_command("docker-compose ps")
        if success:
            if "postgres" in output and "Up" in output:
                self.log("PostgreSQL контейнер: ЗАПУЩЕН", "SUCCESS")
            else:
                self.log("PostgreSQL контейнер: НЕ ЗАПУЩЕН", "WARNING")
                if self.fix:
                    self.log("  Запустить: docker-compose up -d postgres", "INFO")
                    
            if "redis" in output and "Up" in output:
                self.log("Redis контейнер: ЗАПУЩЕН", "SUCCESS")
            else:
                self.log("Redis контейнер: НЕ ЗАПУЩЕН", "WARNING")
                if self.fix:
                    self.log("  Запустить: docker-compose up -d redis", "INFO")
                    
            if "qdrant" in output and "Up" in output:
                self.log("Qdrant контейнер: ЗАПУЩЕН", "SUCCESS")
            else:
                self.log("Qdrant контейнер: НЕ ЗАПУЩЕН", "WARNING")
                if self.fix:
                    self.log("  Запустить: docker-compose up -d qdrant", "INFO")
        else:
            self.log("Не удалось проверить статус контейнеров", "WARNING")
            
    def check_services_connectivity(self):
        """Проверка подключения к сервисам"""
        self.log(f"\n{Colors.BOLD}🔌 ПОДКЛЮЧЕНИЕ К СЕРВИСАМ{Colors.RESET}")
        
        services = [
            ("PostgreSQL", "localhost", 5432),
            ("Redis", "localhost", 6379), 
            ("Qdrant", "localhost", 6333),
        ]
        
        for service_name, host, port in services:
            if self.check_port(host, port):
                self.log(f"{service_name} ({host}:{port}): ДОСТУПЕН", "SUCCESS")
            else:
                self.log(f"{service_name} ({host}:{port}): НЕДОСТУПЕН", "ERROR")
                if self.fix:
                    self.log(f"  Запустить: docker-compose up -d {service_name.lower()}", "INFO")
                    
    def check_api_endpoints(self):
        """Проверка API endpoints"""
        self.log(f"\n{Colors.BOLD}🌐 API ENDPOINTS{Colors.RESET}")
        
        # Проверка основного API
        if self.check_port("localhost", 8000):
            self.log("FastAPI сервер (localhost:8000): ЗАПУЩЕН", "SUCCESS")
            
            # Проверка конкретных endpoints
            endpoints = [
                ("http://localhost:8000/health", "Health Check"),
                ("http://localhost:8000/", "Root Endpoint"),
                ("http://localhost:8000/docs", "Swagger UI"),
                ("http://localhost:8000/redoc", "ReDoc"),
            ]
            
            for url, description in endpoints:
                success, status = self.check_http_endpoint(url)
                if success:
                    self.log(f"  {description}: ДОСТУПЕН", "SUCCESS")
                else:
                    self.log(f"  {description}: НЕДОСТУПЕН ({status})", "ERROR")
        else:
            self.log("FastAPI сервер (localhost:8000): НЕ ЗАПУЩЕН", "ERROR")
            if self.fix:
                self.log("  Запустить: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload", "INFO")
                
    def check_frontend(self):
        """Проверка фронтенда"""
        self.log(f"\n{Colors.BOLD}⚛️  ФРОНТЕНД{Colors.RESET}")
        
        # Проверка Node.js зависимостей
        if self.check_file_exists("frontend/node_modules"):
            self.log("Node.js зависимости: УСТАНОВЛЕНЫ", "SUCCESS")
        else:
            self.log("Node.js зависимости: НЕ УСТАНОВЛЕНЫ", "ERROR")
            if self.fix:
                self.log("  Установить: cd frontend && npm install", "INFO")
                
        # Проверка фронтенд сервера
        if self.check_port("localhost", 3000):
            self.log("React сервер (localhost:3000): ЗАПУЩЕН", "SUCCESS")
            success, status = self.check_http_endpoint("http://localhost:3000")
            if success:
                self.log("  React приложение: ДОСТУПНО", "SUCCESS")
            else:
                self.log(f"  React приложение: НЕДОСТУПНО ({status})", "ERROR")
        else:
            self.log("React сервер (localhost:3000): НЕ ЗАПУЩЕН", "WARNING")
            if self.fix:
                self.log("  Запустить: cd frontend && npm run dev", "INFO")
                
    def check_environment_variables(self):
        """Проверка переменных окружения"""
        self.log(f"\n{Colors.BOLD}🔧 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ{Colors.RESET}")
        
        # Проверка .env файлов
        env_files = [".env.local", ".env", ".env.development"]
        env_found = False
        
        for env_file in env_files:
            if self.check_file_exists(env_file):
                self.log(f"Конфигурация: {env_file}", "SUCCESS")
                env_found = True
                break
                
        if not env_found:
            self.log("Файл конфигурации не найден", "ERROR")
            if self.fix:
                self.log("  Создать: cp env.example .env.local", "INFO")
                
        # Проверка важных переменных
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "QDRANT_HOST",
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Скрываем ключи API
                if "API_KEY" in var:
                    display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                    self.log(f"  {var}: {display_value}", "SUCCESS")
                else:
                    self.log(f"  {var}: {value}", "SUCCESS")
            else:
                self.log(f"  {var}: НЕ УСТАНОВЛЕНА", "ERROR")
                
    def check_database_connection(self):
        """Проверка подключения к базе данных"""
        self.log(f"\n{Colors.BOLD}🗄️  БАЗА ДАННЫХ{Colors.RESET}")
        
        try:
            # Простая проверка подключения к PostgreSQL
            database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_assistant")
            
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.log(f"PostgreSQL подключение: УСПЕШНО", "SUCCESS")
            self.log(f"  Версия: {version.split()[0]} {version.split()[1]}", "VERBOSE")
            
            # Проверка таблиц
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            if tables:
                self.log(f"  Таблицы: {len(tables)} найдено", "SUCCESS")
                for table in tables[:5]:  # Показываем первые 5
                    self.log(f"    - {table[0]}", "VERBOSE")
            else:
                self.log("  Таблицы: НЕ НАЙДЕНЫ", "WARNING")
                if self.fix:
                    self.log("  Создать: alembic upgrade head", "INFO")
                    
            conn.close()
            
        except ImportError:
            self.log("psycopg2 не установлен", "ERROR")
        except Exception as e:
            self.log(f"Ошибка подключения к БД: {str(e)}", "ERROR")
            
    def generate_summary(self):
        """Генерация итогового отчета"""
        self.log(f"\n{Colors.BOLD}📊 ИТОГОВЫЙ ОТЧЕТ{Colors.RESET}")
        
        total_checks = len(self.results)
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        success_count = total_checks - error_count - warning_count
        
        self.log(f"Всего проверок: {total_checks}", "INFO")
        if success_count > 0:
            self.log(f"Успешно: {success_count}", "SUCCESS")
        if warning_count > 0:
            self.log(f"Предупреждения: {warning_count}", "WARNING")
        if error_count > 0:
            self.log(f"Ошибки: {error_count}", "ERROR")
            
        # Общая оценка
        if error_count == 0:
            if warning_count == 0:
                self.log(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ОКРУЖЕНИЕ ПОЛНОСТЬЮ ГОТОВО К РАЗРАБОТКЕ!{Colors.RESET}")
            else:
                self.log(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  ОКРУЖЕНИЕ ПОЧТИ ГОТОВО (есть предупреждения){Colors.RESET}")
        else:
            self.log(f"\n{Colors.RED}{Colors.BOLD}❌ ОКРУЖЕНИЕ ТРЕБУЕТ НАСТРОЙКИ{Colors.RESET}")
            
        # Быстрые команды для исправления
        if error_count > 0:
            self.log(f"\n{Colors.BOLD}🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ:{Colors.RESET}")
            self.log("# Установка зависимостей:")
            self.log("pip install -r requirements.txt")
            self.log("cd frontend && npm install")
            self.log("")
            self.log("# Запуск сервисов:")
            self.log("docker-compose up -d postgres redis qdrant")
            self.log("")
            self.log("# Запуск приложения:")
            self.log("export $(cat .env.local | xargs)")
            self.log("uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
            
    def run_all_checks(self):
        """Запуск всех проверок"""
        self.log(f"{Colors.MAGENTA}{Colors.BOLD}🔍 AI ASSISTANT - ДИАГНОСТИКА ОКРУЖЕНИЯ РАЗРАБОТКИ{Colors.RESET}\n")
        
        try:
            self.check_system_info()
            self.check_required_tools()
            self.check_project_structure()
            self.check_python_environment()
            self.check_environment_variables()
            self.check_docker_services()
            self.check_services_connectivity()
            self.check_database_connection()
            self.check_api_endpoints()
            self.check_frontend()
            self.generate_summary()
            
        except KeyboardInterrupt:
            self.log("\n\nПроверка прервана пользователем", "WARNING")
        except Exception as e:
            self.log(f"\nНеожиданная ошибка: {str(e)}", "ERROR")
            
def main():
    parser = argparse.ArgumentParser(
        description="🔍 Диагностика окружения разработки AI Assistant"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Подробный вывод"
    )
    parser.add_argument(
        "--fix", "-f", 
        action="store_true", 
        help="Показать команды для исправления проблем"
    )
    
    args = parser.parse_args()
    
    checker = EnvironmentChecker(verbose=args.verbose, fix=args.fix)
    checker.run_all_checks()
    
    # Возвращаем код выхода
    if checker.errors:
        sys.exit(1)
    elif checker.warnings:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 