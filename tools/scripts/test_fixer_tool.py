#!/usr/bin/env python3
"""
Test Fixer Tool
Автоматизированный анализ и исправление failed тестов

Usage:
    python tools/scripts/test_fixer_tool.py --analyze
    python tools/scripts/test_fixer_tool.py --fix --category=imports
    python tools/scripts/test_fixer_tool.py --run --pattern="*auth*"
"""

import os
import re
import ast
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TestFailure:
    """Информация о failed тесте"""
    test_name: str
    file_path: str
    error_type: str
    error_message: str
    line_number: Optional[int] = None
    category: str = "unknown"
    fix_priority: str = "medium"
    suggested_fix: str = ""


class TestFailureAnalyzer:
    """Анализатор ошибок тестов"""
    
    def __init__(self):
        self.error_patterns = {
            "imports": [
                r"ModuleNotFoundError: No module named '([^']+)'",
                r"ImportError: cannot import name '([^']+)'",
                r"AttributeError: module '([^']+)' has no attribute '([^']+)'"
            ],
            "attributes": [
                r"AttributeError: '([^']+)' object has no attribute '([^']+)'",
                r"AttributeError: type object '([^']+)' has no attribute '([^']+)'"
            ],
            "async_await": [
                r"TypeError: object dict can't be used in 'await' expression",
                r"AttributeError: 'coroutine' object has no attribute '([^']+)'",
                r"RuntimeWarning: coroutine '([^']+)' was never awaited"
            ],
            "mocks": [
                r"TypeError: ([^()]+)\(\) got an unexpected keyword argument '([^']+)'",
                r"TypeError: ([^()]+)\(\) missing \d+ required positional argument",
                r"TypeError: Can't instantiate abstract class"
            ],
            "enum_comparison": [
                r"AssertionError: assert <([^>]+)> == '([^']+)'",
                r"AssertionError: assert '([^']+)' in <([^>]+)>"
            ],
            "validation": [
                r"pydantic_core\._pydantic_core\.ValidationError",
                r"ValueError: ([^']+)",
                r"TypeError: __init__\(\) missing \d+ required positional argument"
            ]
        }
        
    def categorize_failure(self, error_message: str) -> Tuple[str, str]:
        """Категоризация ошибки и определение приоритета"""
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.MULTILINE):
                    priority = self._get_priority(category)
                    return category, priority
        return "unknown", "low"
        
    def _get_priority(self, category: str) -> str:
        """Определение приоритета исправления"""
        high_priority = ["imports", "attributes", "async_await"]
        medium_priority = ["mocks", "enum_comparison"]
        
        if category in high_priority:
            return "high"
        elif category in medium_priority:
            return "medium"
        else:
            return "low"
            
    def suggest_fix(self, failure: TestFailure) -> str:
        """Предложение исправления"""
        suggestions = {
            "imports": self._suggest_import_fix,
            "attributes": self._suggest_attribute_fix,
            "async_await": self._suggest_async_fix,
            "mocks": self._suggest_mock_fix,
            "enum_comparison": self._suggest_enum_fix,
            "validation": self._suggest_validation_fix
        }
        
        suggest_func = suggestions.get(failure.category)
        if suggest_func:
            return suggest_func(failure)
        return "Требует ручного исправления"
        
    def _suggest_import_fix(self, failure: TestFailure) -> str:
        """Предложение для исправления import ошибок"""
        if "ModuleNotFoundError" in failure.error_message:
            missing_module = re.search(r"No module named '([^']+)'", failure.error_message)
            if missing_module:
                module = missing_module.group(1)
                return f"Добавить недостающий модуль: {module} или исправить import path"
                
        elif "cannot import name" in failure.error_message:
            match = re.search(r"cannot import name '([^']+)' from '([^']+)'", failure.error_message)
            if match:
                name, module = match.groups()
                return f"Проверить экспорт {name} в модуле {module}"
                
        elif "has no attribute" in failure.error_message:
            match = re.search(r"module '([^']+)' has no attribute '([^']+)'", failure.error_message)
            if match:
                module, attr = match.groups()
                return f"Добавить {attr} в модуль {module} или исправить import"
                
        return "Исправить import statement"
        
    def _suggest_attribute_fix(self, failure: TestFailure) -> str:
        """Предложение для исправления attribute ошибок"""
        match = re.search(r"'([^']+)' object has no attribute '([^']+)'", failure.error_message)
        if match:
            obj_type, attr = match.groups()
            return f"Добавить атрибут {attr} в класс {obj_type} или исправить вызов"
        return "Исправить обращение к атрибуту"
        
    def _suggest_async_fix(self, failure: TestFailure) -> str:
        """Предложение для исправления async/await ошибок"""
        if "can't be used in 'await' expression" in failure.error_message:
            return "Убрать await перед sync функцией или сделать функцию async"
        elif "coroutine' object has no attribute" in failure.error_message:
            return "Добавить await перед вызовом async функции"
        elif "was never awaited" in failure.error_message:
            return "Добавить await перед coroutine"
        return "Исправить async/await pattern"
        
    def _suggest_mock_fix(self, failure: TestFailure) -> str:
        """Предложение для исправления mock ошибок"""
        if "unexpected keyword argument" in failure.error_message:
            return "Исправить аргументы в mock setup"
        elif "missing" in failure.error_message and "required" in failure.error_message:
            return "Добавить недостающие аргументы в mock"
        elif "abstract class" in failure.error_message:
            return "Реализовать абстрактные методы или использовать Mock"
        return "Исправить mock configuration"
        
    def _suggest_enum_fix(self, failure: TestFailure) -> str:
        """Предложение для исправления enum сравнений"""
        match = re.search(r"assert <([^>]+)> == '([^']+)'", failure.error_message)
        if match:
            enum_val, string_val = match.groups()
            return f"Использовать {enum_val}.value для сравнения со строкой '{string_val}'"
        return "Исправить сравнение enum с string"
        
    def _suggest_validation_fix(self, failure: TestFailure) -> str:
        """Предложение для исправления validation ошибок"""
        if "ValidationError" in failure.error_message:
            return "Исправить данные для Pydantic модели"
        elif "missing" in failure.error_message and "positional argument" in failure.error_message:
            return "Добавить недостающие аргументы в конструктор"
        return "Исправить валидацию данных"


class TestRunner:
    """Запуск и анализ тестов"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analyzer = TestFailureAnalyzer()
        
    def run_tests(self, pattern: str = "tests/unit/", verbose: bool = True) -> Dict:
        """Запуск тестов с анализом результатов"""
        logger.info(f"🧪 Запуск тестов: {pattern}")
        
        cmd = [
            "python", "-m", "pytest", pattern,
            "--tb=short", "--no-header", "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 минут
                cwd=self.project_root
            )
            
            return self._parse_test_results(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Таймаут при запуске тестов")
            return {"error": "timeout"}
        except Exception as e:
            logger.error(f"❌ Ошибка запуска тестов: {e}")
            return {"error": str(e)}
            
    def _parse_test_results(self, stdout: str, stderr: str) -> Dict:
        """Парсинг результатов тестов"""
        # Статистика из последней строки
        stats_match = re.search(
            r'(\d+) failed,?\s*(\d+) passed,?\s*(?:(\d+) skipped,?)?\s*(?:(\d+) errors?)?',
            stdout
        )
        
        stats = {
            "failed": 0, "passed": 0, "skipped": 0, "errors": 0
        }
        
        if stats_match:
            stats["failed"] = int(stats_match.group(1) or 0)
            stats["passed"] = int(stats_match.group(2) or 0) 
            stats["skipped"] = int(stats_match.group(3) or 0)
            stats["errors"] = int(stats_match.group(4) or 0)
            
        # Парсинг failed тестов
        failures = self._extract_failures(stdout + stderr)
        
        return {
            "stats": stats,
            "failures": failures,
            "success_rate": stats["passed"] / (stats["passed"] + stats["failed"]) * 100 if (stats["passed"] + stats["failed"]) > 0 else 0
        }
        
    def _extract_failures(self, output: str) -> List[TestFailure]:
        """Извлечение информации о failed тестах"""
        failures = []
        
        # Разделение на блоки тестов
        test_blocks = re.split(r'^FAILED ', output, flags=re.MULTILINE)
        
        for block in test_blocks[1:]:  # Пропускаем первый блок (до первого FAILED)
            failure = self._parse_failure_block(block)
            if failure:
                failures.append(failure)
                
        return failures
        
    def _parse_failure_block(self, block: str) -> Optional[TestFailure]:
        """Парсинг блока с информацией о failed тесте"""
        lines = block.strip().split('\n')
        if not lines:
            return None
            
        # Первая строка содержит имя теста
        test_line = lines[0]
        test_match = re.match(r'([^:]+)::', test_line)
        
        if not test_match:
            return None
            
        test_name = test_match.group(1)
        file_path = test_name.split('::')[0] if '::' in test_name else test_name
        
        # Поиск ошибки
        error_message = '\n'.join(lines)
        
        # Определение типа ошибки
        error_type = "Unknown"
        if "AttributeError" in error_message:
            error_type = "AttributeError"
        elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
            error_type = "ImportError"
        elif "TypeError" in error_message:
            error_type = "TypeError"
        elif "AssertionError" in error_message:
            error_type = "AssertionError"
            
        # Категоризация
        category, priority = self.analyzer.categorize_failure(error_message)
        
        failure = TestFailure(
            test_name=test_name,
            file_path=file_path,
            error_type=error_type,
            error_message=error_message,
            category=category,
            fix_priority=priority
        )
        
        # Предложение исправления
        failure.suggested_fix = self.analyzer.suggest_fix(failure)
        
        return failure


class TestFixer:
    """Автоматическое исправление тестов"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        
    def fix_import_errors(self, failures: List[TestFailure]) -> int:
        """Автоматическое исправление import ошибок"""
        fixed_count = 0
        
        import_failures = [f for f in failures if f.category == "imports"]
        logger.info(f"🔧 Исправление {len(import_failures)} import ошибок")
        
        for failure in import_failures:
            if self._fix_single_import(failure):
                fixed_count += 1
                
        return fixed_count
        
    def _fix_single_import(self, failure: TestFailure) -> bool:
        """Исправление одной import ошибки"""
        try:
            file_path = self.project_root / failure.file_path
            if not file_path.exists():
                return False
                
            content = file_path.read_text(encoding='utf-8')
            
            # Различные стратегии исправления
            if "No module named" in failure.error_message:
                content = self._fix_missing_module(content, failure)
            elif "cannot import name" in failure.error_message:
                content = self._fix_import_name(content, failure)
            elif "has no attribute" in failure.error_message:
                content = self._fix_attribute_import(content, failure)
                
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"✅ Исправлен import в {failure.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка исправления {failure.file_path}: {e}")
            return False
            
    def _fix_missing_module(self, content: str, failure: TestFailure) -> str:
        """Исправление недостающего модуля"""
        # Простая замена известных неправильных путей
        replacements = {
            "from llm import": "from adapters.llm import",
            "from app.domain import": "from domain import",
            "import app.domain": "import domain",
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
            
        return content
        
    def _fix_import_name(self, content: str, failure: TestFailure) -> str:
        """Исправление неправильного имени import"""
        # Здесь можно добавить логику исправления имен
        return content
        
    def _fix_attribute_import(self, content: str, failure: TestFailure) -> str:
        """Исправление неправильного атрибута"""
        # Здесь можно добавить логику исправления атрибутов
        return content
        
    def fix_enum_comparisons(self, failures: List[TestFailure]) -> int:
        """Автоматическое исправление enum сравнений"""
        fixed_count = 0
        
        enum_failures = [f for f in failures if f.category == "enum_comparison"]
        logger.info(f"🔧 Исправление {len(enum_failures)} enum сравнений")
        
        for failure in enum_failures:
            if self._fix_single_enum(failure):
                fixed_count += 1
                
        return fixed_count
        
    def _fix_single_enum(self, failure: TestFailure) -> bool:
        """Исправление одного enum сравнения"""
        try:
            file_path = self.project_root / failure.file_path
            content = file_path.read_text(encoding='utf-8')
            
            # Замена сравнений enum со строкой на .value
            patterns = [
                (r'assert\s+([^=]+)\s*==\s*["\']([^"\']+)["\']', r'assert \1.value == "\2"'),
                (r'([^=]+)\s*==\s*["\']([^"\']+)["\']', r'\1.value == "\2"'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
                
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"✅ Исправлены enum сравнения в {failure.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка исправления enum в {failure.file_path}: {e}")
            return False


class TestFixerTool:
    """Основной инструмент исправления тестов"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.runner = TestRunner(project_root)
        self.fixer = TestFixer(project_root)
        
    def analyze_test_failures(self, pattern: str = "tests/unit/") -> Dict:
        """Анализ failed тестов"""
        logger.info("🔍 Анализ failed тестов...")
        
        results = self.runner.run_tests(pattern)
        
        if "error" in results:
            return results
            
        # Группировка по категориям
        by_category = defaultdict(list)
        for failure in results["failures"]:
            by_category[failure.category].append(failure)
            
        # Группировка по приоритету
        by_priority = defaultdict(list)
        for failure in results["failures"]:
            by_priority[failure.fix_priority].append(failure)
            
        analysis = {
            "stats": results["stats"],
            "success_rate": results["success_rate"],
            "total_failures": len(results["failures"]),
            "by_category": dict(by_category),
            "by_priority": dict(by_priority),
            "failures": results["failures"]
        }
        
        return analysis
        
    def print_analysis_report(self, analysis: Dict):
        """Печать детального отчета анализа"""
        print("\n" + "="*60)
        print("🧪 TEST FAILURE ANALYSIS")
        print("="*60)
        
        stats = analysis["stats"]
        print(f"📊 Статистика тестов:")
        print(f"   ✅ Passed: {stats['passed']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   ⚠️  Skipped: {stats['skipped']}")
        print(f"   🚫 Errors: {stats['errors']}")
        print(f"   📈 Success Rate: {analysis['success_rate']:.1f}%")
        
        print(f"\n📋 Ошибки по категориям:")
        for category, failures in analysis["by_category"].items():
            if failures:
                print(f"\n🔥 {category.upper()} ({len(failures)} ошибок):")
                for failure in failures[:3]:  # Показываем первые 3
                    print(f"   ❌ {failure.test_name}")
                    print(f"      {failure.error_type}: {failure.suggested_fix}")
                if len(failures) > 3:
                    print(f"   ... и еще {len(failures) - 3} ошибок")
                    
        print(f"\n🎯 Ошибки по приоритету:")
        for priority in ["high", "medium", "low"]:
            failures = analysis["by_priority"].get(priority, [])
            if failures:
                print(f"   🔥 {priority.upper()}: {len(failures)} ошибок")
                
    def fix_by_category(self, category: str, analysis: Dict = None) -> int:
        """Исправление ошибок по категории"""
        if analysis is None:
            analysis = self.analyze_test_failures()
            
        failures = analysis["by_category"].get(category, [])
        
        if not failures:
            logger.info(f"Нет ошибок категории {category}")
            return 0
            
        logger.info(f"🔧 Исправление {len(failures)} ошибок категории {category}")
        
        fixed_count = 0
        
        if category == "imports":
            fixed_count = self.fixer.fix_import_errors(failures)
        elif category == "enum_comparison":
            fixed_count = self.fixer.fix_enum_comparisons(failures)
        else:
            logger.warning(f"Автоматическое исправление для категории {category} не реализовано")
            
        return fixed_count
        
    def fix_by_priority(self, priority: str = "high") -> int:
        """Исправление ошибок по приоритету"""
        analysis = self.analyze_test_failures()
        failures = analysis["by_priority"].get(priority, [])
        
        if not failures:
            logger.info(f"Нет ошибок приоритета {priority}")
            return 0
            
        # Группируем по категориям и исправляем
        by_category = defaultdict(list)
        for failure in failures:
            by_category[failure.category].append(failure)
            
        total_fixed = 0
        for category, cat_failures in by_category.items():
            fixed = self.fix_by_category(category, {"by_category": {category: cat_failures}})
            total_fixed += fixed
            
        return total_fixed


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(description="Test Fixer Tool")
    parser.add_argument("--analyze", action="store_true", help="Анализировать failed тесты")
    parser.add_argument("--fix", action="store_true", help="Исправить тесты")
    parser.add_argument("--run", action="store_true", help="Запустить тесты")
    parser.add_argument("--category", choices=["imports", "attributes", "async_await", "mocks", "enum_comparison", "validation"], 
                       help="Категория ошибок для исправления")
    parser.add_argument("--priority", choices=["high", "medium", "low"], 
                       default="high", help="Приоритет ошибок для исправления")
    parser.add_argument("--pattern", default="tests/unit/", help="Паттерн для поиска тестов")
    
    args = parser.parse_args()
    
    tool = TestFixerTool()
    
    if args.analyze:
        analysis = tool.analyze_test_failures(args.pattern)
        tool.print_analysis_report(analysis)
        
    elif args.fix:
        if args.category:
            fixed = tool.fix_by_category(args.category)
            print(f"\n🎉 Исправлено {fixed} ошибок категории {args.category}")
        else:
            fixed = tool.fix_by_priority(args.priority)
            print(f"\n🎉 Исправлено {fixed} ошибок приоритета {args.priority}")
            
    elif args.run:
        results = tool.runner.run_tests(args.pattern)
        if "stats" in results:
            stats = results["stats"]
            print(f"\n📊 Результаты тестов:")
            print(f"   ✅ Passed: {stats['passed']}")
            print(f"   ❌ Failed: {stats['failed']}")
            print(f"   ⚠️  Skipped: {stats['skipped']}")
            print(f"   📈 Success Rate: {results['success_rate']:.1f}%")
        else:
            print(f"\n❌ Ошибка запуска тестов: {results.get('error', 'Unknown')}")
            
    else:
        print("Используйте --analyze, --fix или --run")
        parser.print_help()


if __name__ == "__main__":
    main() 