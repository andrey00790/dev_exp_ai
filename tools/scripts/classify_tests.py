#!/usr/bin/env python3
"""
🧪 TEST CLASSIFICATION AND REORGANIZATION SCRIPT
Анализирует и переносит тесты в соответствующие директории следуя Context7 best practices.

Типы тестов:
- unit: изолированная логика, мокированные зависимости
- integration: взаимодействие между модулями, с БД/API  
- e2e: полные пользовательские сценарии
- smoke: базовые проверки "живости" ключевых функций
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Set
import ast
import subprocess

class TestClassifier:
    """Классификатор тестов на основе содержимого и структуры"""
    
    def __init__(self, tests_dir: str = "tests"):
        self.tests_dir = Path(tests_dir)
        self.classification_patterns = {
            'unit': [
                r'unittest\.mock|from unittest\.mock import|mock\.',
                r'@pytest\.fixture.*scope.*function',
                r'AsyncMock|MagicMock|Mock\(\)',
                r'with.*patch\(',
                r'test.*utils?|test.*core|test.*async',
                r'TestClient.*mock',
                r'isolated.*test|pure.*logic'
            ],
            'integration': [
                r'psycopg2|sqlalchemy|database',
                r'redis|qdrant|elasticsearch',
                r'requests\.|httpx\.|aiohttp',
                r'docker|container',
                r'test.*integration|integration.*test',
                r'@pytest\.mark\.integration',
                r'real.*service|external.*api'
            ],
            'e2e': [
                r'TestClient\(app\)|FastAPI.*test',
                r'selenium|playwright|cypress',
                r'test.*workflow|full.*workflow',
                r'end.*to.*end|e2e',
                r'complete.*scenario|user.*journey',
                r'test.*comprehensive|comprehensive.*test',
                r'@pytest\.mark\.e2e'
            ],
            'smoke': [
                r'health.*check|test.*health',
                r'status.*endpoint|ping.*test',
                r'basic.*connectivity|simple.*test',
                r'smoke.*test|@pytest\.mark\.smoke',
                r'quick.*check|sanity.*test'
            ]
        }
        
        self.filename_patterns = {
            'unit': [
                r'test_.*utils?\.py$',
                r'test_.*core\.py$', 
                r'test_.*async.*patterns\.py$',
                r'test_.*models?\.py$',
                r'test_.*services?\.py$'
            ],
            'integration': [
                r'test_.*integration\.py$',
                r'test_.*qdrant.*\.py$',
                r'test_.*postgres.*\.py$',
                r'test_.*redis.*\.py$',
                r'test_.*database.*\.py$'
            ],
            'e2e': [
                r'test_.*e2e\.py$',
                r'test_.*comprehensive\.py$',
                r'test_.*workflow\.py$',
                r'test_.*end.*to.*end\.py$'
            ],
            'smoke': [
                r'test_.*health\.py$',
                r'test_.*smoke\.py$',
                r'test_.*quick\.py$',
                r'test_.*basic\.py$'
            ]
        }
        
    def analyze_file_content(self, file_path: Path) -> Tuple[str, float]:
        """Анализирует содержимое файла и возвращает тип теста с уверенностью"""
        try:
            content = file_path.read_text(encoding='utf-8')
            scores = {test_type: 0 for test_type in self.classification_patterns}
            
            # Анализ содержимого
            for test_type, patterns in self.classification_patterns.items():
                for pattern in patterns:
                    matches = len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                    scores[test_type] += matches
            
            # Анализ имени файла
            filename = file_path.name
            for test_type, patterns in self.filename_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, filename, re.IGNORECASE):
                        scores[test_type] += 5  # Имя файла важнее
            
            # Специальные правила
            if 'testclient' in content.lower() and 'mock' in content.lower():
                scores['unit'] += 3
            elif 'testclient' in content.lower() and 'app' in content.lower():
                scores['e2e'] += 3
                
            if 'pytest.mark.asyncio' in content and 'database' not in content.lower():
                scores['unit'] += 2
                
            # Определяем лучший тип
            best_type = max(scores, key=scores.get)
            confidence = scores[best_type] / max(sum(scores.values()), 1)
            
            return best_type, confidence
            
        except Exception as e:
            print(f"❌ Ошибка анализа {file_path}: {e}")
            return 'unit', 0.0
    
    def find_test_files(self) -> List[Path]:
        """Находит все тестовые файлы в корне tests/"""
        test_files = []
        for file_path in self.tests_dir.iterdir():
            if (file_path.is_file() and 
                file_path.name.startswith('test_') and 
                file_path.suffix == '.py' and
                file_path.name != 'conftest.py'):
                test_files.append(file_path)
        return test_files
    
    def classify_all_tests(self) -> Dict[str, List[Tuple[Path, float]]]:
        """Классифицирует все тесты"""
        test_files = self.find_test_files()
        classified = {
            'unit': [],
            'integration': [],
            'e2e': [],
            'smoke': []
        }
        
        print(f"🔍 Найдено {len(test_files)} тестовых файлов для анализа")
        
        for file_path in test_files:
            test_type, confidence = self.analyze_file_content(file_path)
            classified[test_type].append((file_path, confidence))
            print(f"📁 {file_path.name} → {test_type} (уверенность: {confidence:.2f})")
        
        return classified
    
    def create_directories(self):
        """Создает необходимые директории"""
        for test_type in ['unit', 'integration', 'e2e', 'smoke']:
            target_dir = self.tests_dir / test_type
            target_dir.mkdir(exist_ok=True)
            
            # Создаем __init__.py если его нет
            init_file = target_dir / '__init__.py'
            if not init_file.exists():
                init_file.write_text('"""Tests for the AI Assistant project."""\n')
    
    def move_tests(self, classified: Dict[str, List[Tuple[Path, float]]], 
                   min_confidence: float = 0.1, dry_run: bool = False) -> Dict[str, int]:
        """Перемещает тесты в соответствующие директории"""
        
        if dry_run:
            print("\n🧪 DRY RUN MODE - файлы НЕ будут перемещены")
        
        moved_count = {'unit': 0, 'integration': 0, 'e2e': 0, 'smoke': 0}
        
        for test_type, files in classified.items():
            target_dir = self.tests_dir / test_type
            
            for file_path, confidence in files:
                if confidence < min_confidence:
                    print(f"⚠️  Пропускаем {file_path.name} - низкая уверенность ({confidence:.2f})")
                    continue
                
                target_path = target_dir / file_path.name
                
                # Проверяем конфликты
                if target_path.exists():
                    print(f"⚠️  Конфликт: {target_path} уже существует")
                    # Создаем бэкап имя
                    counter = 1
                    while target_path.exists():
                        name_parts = file_path.stem, counter, file_path.suffix
                        target_path = target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                        counter += 1
                
                if dry_run:
                    print(f"📁 [DRY] {file_path} → {target_path}")
                else:
                    try:
                        shutil.move(str(file_path), str(target_path))
                        print(f"✅ Перемещен: {file_path.name} → {test_type}/")
                        moved_count[test_type] += 1
                    except Exception as e:
                        print(f"❌ Ошибка перемещения {file_path}: {e}")
        
        return moved_count
    
    def update_imports_in_moved_tests(self, moved_files: Dict[str, List[str]]):
        """Обновляет импорты в перемещенных тестах"""
        print("\n🔧 Обновление импортов...")
        
        # Паттерны для обновления импортов
        import_updates = [
            (r'from tests\.conftest import', r'from ..conftest import'),
            (r'from tests\.(.+) import', r'from ..\\1 import'),
            (r'import tests\.(.+)', r'import tests.\\1'),  # Оставляем абсолютные импорты для tests.*
        ]
        
        for test_type, files in moved_files.items():
            for filename in files:
                file_path = self.tests_dir / test_type / filename
                if not file_path.exists():
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    original_content = content
                    
                    for pattern, replacement in import_updates:
                        content = re.sub(pattern, replacement, content)
                    
                    if content != original_content:
                        file_path.write_text(content, encoding='utf-8')
                        print(f"📝 Обновлены импорты в {test_type}/{filename}")
                        
                except Exception as e:
                    print(f"⚠️  Ошибка обновления импортов в {file_path}: {e}")
    
    def generate_summary_report(self, classified: Dict[str, List[Tuple[Path, float]]], 
                              moved_count: Dict[str, int]) -> str:
        """Генерирует отчет о классификации"""
        
        total_files = sum(len(files) for files in classified.values())
        total_moved = sum(moved_count.values())
        
        report = [
            "\n" + "="*60,
            "📊 ОТЧЕТ О КЛАССИФИКАЦИИ И РЕОРГАНИЗАЦИИ ТЕСТОВ",
            "="*60,
            f"📁 Всего проанализировано файлов: {total_files}",
            f"📁 Всего перемещено файлов: {total_moved}",
            ""
        ]
        
        for test_type, files in classified.items():
            report.append(f"🧪 {test_type.upper()}:")
            report.append(f"   Найдено: {len(files)}")
            report.append(f"   Перемещено: {moved_count[test_type]}")
            
            if files:
                report.append("   Файлы:")
                for file_path, confidence in sorted(files, key=lambda x: x[1], reverse=True):
                    status = "✅" if confidence >= 0.1 else "⚠️"
                    report.append(f"     {status} {file_path.name} (уверенность: {confidence:.2f})")
            report.append("")
        
        # Рекомендации
        report.extend([
            "💡 РЕКОМЕНДАЦИИ:",
            "1. Проверьте импорты в перемещенных файлах",
            "2. Запустите тесты для проверки работоспособности",
            "3. Обновите CI/CD конфигурации если нужно",
            "4. Рассмотрите файлы с низкой уверенностью классификации"
        ])
        
        return "\n".join(report)

def check_existing_structure():
    """Проверяет существующую структуру тестов"""
    tests_dir = Path("tests")
    
    if not tests_dir.exists():
        print("❌ Директория tests/ не найдена!")
        return False
    
    existing_dirs = [d.name for d in tests_dir.iterdir() if d.is_dir()]
    expected_dirs = ['unit', 'integration', 'e2e', 'smoke']
    
    print(f"📁 Существующие поддиректории: {existing_dirs}")
    print(f"📁 Ожидаемые поддиректории: {expected_dirs}")
    
    return True

def update_pytest_config():
    """Обновляет pytest конфигурацию"""
    config_content = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov=domain
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    unit: Unit tests (isolated logic, mocked dependencies)
    integration: Integration tests (database, external APIs)
    e2e: End-to-end tests (full user scenarios)
    smoke: Smoke tests (basic health checks)
    slow: Tests that take more than 1 second
    asyncio: Async tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
"""
    
    config_file = Path("pytest.ini")
    config_file.write_text(config_content)
    print("✅ Обновлен pytest.ini")

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Классификация и реорганизация тестов")
    parser.add_argument('--dry-run', action='store_true', help='Режим симуляции без изменений')
    parser.add_argument('--min-confidence', type=float, default=0.1, 
                       help='Минимальная уверенность для перемещения файла')
    parser.add_argument('--update-config', action='store_true', 
                       help='Обновить pytest конфигурацию')
    
    args = parser.parse_args()
    
    print("🧪 КЛАССИФИКАЦИЯ И РЕОРГАНИЗАЦИЯ ТЕСТОВ")
    print("=" * 50)
    
    if not check_existing_structure():
        return 1
    
    # Инициализируем классификатор
    classifier = TestClassifier()
    
    # Создаем директории
    classifier.create_directories()
    
    # Классифицируем тесты
    classified = classifier.classify_all_tests()
    
    if not any(classified.values()):
        print("ℹ️  Нет файлов для перемещения")
        return 0
    
    # Перемещаем тесты
    moved_count = classifier.move_tests(classified, args.min_confidence, args.dry_run)
    
    # Обновляем импорты если не dry-run
    if not args.dry_run and moved_count:
        moved_files = {
            test_type: [fp.name for fp, conf in files if conf >= args.min_confidence]
            for test_type, files in classified.items()
        }
        classifier.update_imports_in_moved_tests(moved_files)
    
    # Обновляем конфигурацию pytest
    if args.update_config:
        update_pytest_config()
    
    # Генерируем отчет
    report = classifier.generate_summary_report(classified, moved_count)
    print(report)
    
    # Сохраняем отчет
    if not args.dry_run:
        report_file = Path("tests/classification_report.txt")
        report_file.write_text(report)
        print(f"\n💾 Отчет сохранен в {report_file}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 