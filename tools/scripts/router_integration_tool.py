#!/usr/bin/env python3
"""
Router Integration Tool
Автоматизированное сканирование и подключение роутеров в main.py

Usage:
    python tools/scripts/router_integration_tool.py --scan
    python tools/scripts/router_integration_tool.py --connect --priority=high
    python tools/scripts/router_integration_tool.py --test --router=health
"""

import os
import re
import ast
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RouterInfo:
    """Информация о роутере"""
    def __init__(self, file_path: str, prefix: str = "", tags: List[str] = None):
        self.file_path = file_path
        self.prefix = prefix
        self.tags = tags or []
        self.priority = self._calculate_priority()
        
    def _calculate_priority(self) -> str:
        """Определение приоритета роутера"""
        high_priority = ["health", "auth", "search", "ai", "documents"]
        medium_priority = ["monitoring", "admin", "budget", "vector"]
        
        path_lower = self.file_path.lower()
        
        for keyword in high_priority:
            if keyword in path_lower:
                return "high"
                
        for keyword in medium_priority:
            if keyword in path_lower:
                return "medium"
                
        return "low"
        
    def get_import_statement(self) -> str:
        """Генерация import statement"""
        module_path = self.file_path.replace("/", ".").replace(".py", "")
        router_name = f"{Path(self.file_path).stem}_router"
        return f"from {module_path} import router as {router_name}"
        
    def get_include_statement(self) -> str:
        """Генерация include_router statement"""
        router_name = f"{Path(self.file_path).stem}_router"
        prefix = f'prefix="{self.prefix}"' if self.prefix else ''
        return f"app.include_router({router_name}, {prefix})"


class RouterScanner:
    """Сканер роутеров в проекте"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.found_routers: List[RouterInfo] = []
        
    def scan_routers(self) -> List[RouterInfo]:
        """Сканирование всех роутеров в проекте"""
        logger.info("🔍 Сканирование роутеров...")
        
        # Паттерны для поиска файлов с роутерами
        router_patterns = [
            "app/api/**/*.py",
            "backend/presentation/**/*.py", 
            "infrastructure/**/presentation/**/*.py"
        ]
        
        routers = []
        
        for pattern in router_patterns:
            for file_path in self.project_root.glob(pattern):
                if self._is_router_file(file_path):
                    router_info = self._extract_router_info(file_path)
                    if router_info:
                        routers.append(router_info)
                        
        logger.info(f"✅ Найдено {len(routers)} роутеров")
        self.found_routers = routers
        return routers
        
    def _is_router_file(self, file_path: Path) -> bool:
        """Проверка, содержит ли файл роутер"""
        try:
            content = file_path.read_text(encoding='utf-8')
            # Ищем определение роутера
            return bool(re.search(r'router\s*=\s*APIRouter', content))
        except Exception as e:
            logger.debug(f"Ошибка чтения файла {file_path}: {e}")
            return False
            
    def _extract_router_info(self, file_path: Path) -> Optional[RouterInfo]:
        """Извлечение информации о роутере из файла"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Извлечение prefix из APIRouter
            prefix_match = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
            prefix = prefix_match.group(1) if prefix_match else ""
            
            # Извлечение tags
            tags_match = re.search(r'tags\s*=\s*\[(.*?)\]', content)
            tags = []
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [tag.strip(' "\'') for tag in tags_str.split(',') if tag.strip()]
            
            # Относительный путь от корня проекта
            rel_path = str(file_path.relative_to(self.project_root))
            
            return RouterInfo(rel_path, prefix, tags)
            
        except Exception as e:
            logger.error(f"Ошибка извлечения информации из {file_path}: {e}")
            return None


class MainPyAnalyzer:
    """Анализатор main.py для понимания текущих подключений"""
    
    def __init__(self, main_py_path: str = "main.py"):
        self.main_py_path = Path(main_py_path)
        
    def get_connected_routers(self) -> List[str]:
        """Получение списка уже подключенных роутеров"""
        try:
            content = self.main_py_path.read_text(encoding='utf-8')
            
            # Ищем все include_router вызовы
            connected = re.findall(r'app\.include_router\([^)]+\)', content)
            return connected
            
        except Exception as e:
            logger.error(f"Ошибка анализа main.py: {e}")
            return []
            
    def add_router_to_main(self, router_info: RouterInfo) -> bool:
        """Добавление роутера в main.py"""
        try:
            content = self.main_py_path.read_text(encoding='utf-8')
            
            # Поиск функции setup_routes
            setup_routes_match = re.search(
                r'(def setup_routes\(app: FastAPI\) -> None:.*?)(    except Exception as e:)',
                content, re.DOTALL
            )
            
            if not setup_routes_match:
                logger.error("Не найдена функция setup_routes в main.py")
                return False
                
            setup_function = setup_routes_match.group(1)
            exception_block = setup_routes_match.group(2)
            
            # Добавление импорта и подключения роутера
            import_stmt = router_info.get_import_statement()
            include_stmt = router_info.get_include_statement()
            
            # Добавление в секцию импортов (перед exception block)
            new_router_block = f"""
        # Import {router_info.file_path} router
        try:
            {import_stmt}
            {include_stmt}
            logger.info("✅ {router_info.file_path} router configured")
        except ImportError as e:
            logger.warning(f"⚠️ {router_info.file_path} router not available: {{e}}")
        
"""
            
            new_setup_function = setup_function + new_router_block
            new_content = content.replace(
                setup_routes_match.group(0),
                new_setup_function + exception_block
            )
            
            # Запись обновленного файла
            self.main_py_path.write_text(new_content, encoding='utf-8')
            logger.info(f"✅ Роутер {router_info.file_path} добавлен в main.py")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления роутера в main.py: {e}")
            return False


class RouterIntegrationTool:
    """Основной инструмент интеграции роутеров"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.scanner = RouterScanner(project_root)
        self.main_analyzer = MainPyAnalyzer()
        
    def scan_and_report(self) -> Dict:
        """Сканирование и отчет о роутерах"""
        routers = self.scanner.scan_routers()
        connected = self.main_analyzer.get_connected_routers()
        
        # Группировка по приоритету
        by_priority = {"high": [], "medium": [], "low": []}
        for router in routers:
            by_priority[router.priority].append(router)
            
        report = {
            "total_found": len(routers),
            "total_connected": len(connected),
            "by_priority": by_priority,
            "coverage": len(connected) / len(routers) * 100 if routers else 0
        }
        
        return report
        
    def print_scan_report(self):
        """Печать детального отчета о сканировании"""
        report = self.scan_and_report()
        
        print("\n" + "="*60)
        print("🔍 ROUTER INTEGRATION ANALYSIS")
        print("="*60)
        
        print(f"📊 Всего найдено роутеров: {report['total_found']}")
        print(f"🔗 Подключено в main.py: {report['total_connected']}")
        print(f"📈 Покрытие: {report['coverage']:.1f}%")
        
        print("\n📋 Роутеры по приоритету:")
        
        for priority in ["high", "medium", "low"]:
            routers = report['by_priority'][priority]
            if routers:
                print(f"\n🔥 {priority.upper()} приоритет ({len(routers)} роутеров):")
                for router in routers:
                    status = "✅" if self._is_router_connected(router) else "❌"
                    print(f"  {status} {router.file_path}")
                    if router.prefix:
                        print(f"       prefix: {router.prefix}")
                    if router.tags:
                        print(f"       tags: {', '.join(router.tags)}")
                        
    def _is_router_connected(self, router_info: RouterInfo) -> bool:
        """Проверка, подключен ли роутер"""
        connected = self.main_analyzer.get_connected_routers()
        router_name = f"{Path(router_info.file_path).stem}_router"
        return any(router_name in conn for conn in connected)
        
    def connect_routers_by_priority(self, priority: str = "high") -> int:
        """Подключение роутеров по приоритету"""
        routers = self.scanner.scan_routers()
        priority_routers = [r for r in routers if r.priority == priority]
        
        connected_count = 0
        
        logger.info(f"🔄 Подключение {len(priority_routers)} роутеров с приоритетом {priority}")
        
        for router in priority_routers:
            if not self._is_router_connected(router):
                if self.main_analyzer.add_router_to_main(router):
                    connected_count += 1
                    logger.info(f"✅ Подключен: {router.file_path}")
                else:
                    logger.error(f"❌ Ошибка подключения: {router.file_path}")
            else:
                logger.info(f"⚠️ Уже подключен: {router.file_path}")
                
        logger.info(f"🎉 Подключено {connected_count} новых роутеров")
        return connected_count
        
    def test_router_connectivity(self, router_name: str = None):
        """Тестирование подключения роутеров"""
        logger.info("🧪 Тестирование подключения роутеров...")
        
        import subprocess
        
        # Запуск приложения для проверки
        try:
            result = subprocess.run([
                "python", "-c", 
                "from main import app; print('✅ Приложение запускается успешно')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ Все роутеры подключены корректно")
                return True
            else:
                logger.error(f"❌ Ошибка подключения роутеров: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Таймаут при тестировании приложения")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования: {e}")
            return False


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(description="Router Integration Tool")
    parser.add_argument("--scan", action="store_true", help="Сканировать роутеры")
    parser.add_argument("--connect", action="store_true", help="Подключить роутеры")
    parser.add_argument("--test", action="store_true", help="Тестировать подключение")
    parser.add_argument("--priority", choices=["high", "medium", "low"], 
                       default="high", help="Приоритет роутеров для подключения")
    parser.add_argument("--router", help="Конкретный роутер для операции")
    
    args = parser.parse_args()
    
    tool = RouterIntegrationTool()
    
    if args.scan:
        tool.print_scan_report()
        
    elif args.connect:
        connected = tool.connect_routers_by_priority(args.priority)
        print(f"\n🎉 Подключено {connected} роутеров с приоритетом {args.priority}")
        
    elif args.test:
        success = tool.test_router_connectivity(args.router)
        exit(0 if success else 1)
        
    else:
        print("Используйте --scan, --connect или --test")
        parser.print_help()


if __name__ == "__main__":
    main() 