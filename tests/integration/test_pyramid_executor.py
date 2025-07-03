"""
Test Pyramid Executor for AI Assistant MVP
Координирует выполнение всех уровней пирамиды тестирования:
- Unit Tests (база пирамиды)
- Integration Tests (средний уровень)
- E2E Tests (вершина пирамиды)
- Performance/Load Tests (специальные тесты)
"""

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Результат выполнения тестов"""
    test_type: str
    passed: int
    failed: int
    skipped: int
    duration: float
    coverage: float = 0.0
    exit_code: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

class TestPyramidExecutor:
    """Исполнитель пирамиды тестирования"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
    def run_unit_tests(self) -> TestResult:
        """
        Запуск Unit-тестов (база пирамиды)
        Быстрые тесты отдельных компонентов и функций
        """
        logger.info("🔬 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/",
            "--cov=app",
            "--cov=models", 
            "--cov=services",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/unit",
            "--cov-report=json:htmlcov/unit-coverage.json",
            "--json-report",
            "--json-report-file=test-results/unit-results.json",
            "-v",
            "--tb=short",
            "--durations=10"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        # Парсинг результатов
        passed, failed, skipped = self._parse_pytest_output(result.stdout)
        coverage = self._extract_coverage("htmlcov/unit-coverage.json")
        
        test_result = TestResult(
            test_type="Unit Tests",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            coverage=coverage,
            exit_code=result.returncode,
            details={
                "stdout": result.stdout[-1000:],  # Последние 1000 символов
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
        )
        
        self.results.append(test_result)
        self._log_test_result(test_result)
        return test_result
    
    def run_integration_tests(self) -> TestResult:
        """
        Запуск интеграционных тестов (средний уровень)
        Тестирование взаимодействия компонентов
        """
        logger.info("🔄 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/",
            "--cov=app",
            "--cov-report=html:htmlcov/integration",
            "--cov-report=json:htmlcov/integration-coverage.json",
            "--json-report",
            "--json-report-file=test-results/integration-results.json",
            "-v",
            "--tb=short",
            "--durations=10",
            "-x"  # Остановка при первой ошибке для интеграционных тестов
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        passed, failed, skipped = self._parse_pytest_output(result.stdout)
        coverage = self._extract_coverage("htmlcov/integration-coverage.json")
        
        test_result = TestResult(
            test_type="Integration Tests",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            coverage=coverage,
            exit_code=result.returncode,
            details={
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
        )
        
        self.results.append(test_result)
        self._log_test_result(test_result)
        return test_result
    
    def run_e2e_tests(self) -> TestResult:
        """
        Запуск E2E тестов (вершина пирамиды) 
        Полное тестирование пользовательских сценариев
        """
        logger.info("🎯 Running E2E Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/e2e/",
            "--json-report",
            "--json-report-file=test-results/e2e-results.json",
            "-v",
            "--tb=short",
            "--durations=10",
            "-x"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        passed, failed, skipped = self._parse_pytest_output(result.stdout)
        
        test_result = TestResult(
            test_type="E2E Tests",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            exit_code=result.returncode,
            details={
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
        )
        
        self.results.append(test_result)
        self._log_test_result(test_result)
        return test_result
    
    def run_performance_tests(self) -> TestResult:
        """
        Запуск нагрузочных тестов
        Тестирование производительности и стабильности
        """
        logger.info("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/performance/",
            "--json-report",
            "--json-report-file=test-results/performance-results.json",
            "-v",
            "--tb=short",
            "--durations=10"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        passed, failed, skipped = self._parse_pytest_output(result.stdout)
        
        test_result = TestResult(
            test_type="Performance Tests",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            exit_code=result.returncode,
            details={
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
        )
        
        self.results.append(test_result)
        self._log_test_result(test_result)
        return test_result
    
    def run_smoke_tests(self) -> TestResult:
        """
        Запуск smoke тестов
        Базовая проверка критичной функциональности
        """
        logger.info("💨 Running Smoke Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/smoke/",
            "--json-report",
            "--json-report-file=test-results/smoke-results.json",
            "-v",
            "--tb=line"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        passed, failed, skipped = self._parse_pytest_output(result.stdout)
        
        test_result = TestResult(
            test_type="Smoke Tests",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            exit_code=result.returncode,
            details={
                "stdout": result.stdout[-1000:],
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
        )
        
        self.results.append(test_result)
        self._log_test_result(test_result)
        return test_result
    
    def run_full_pyramid(self, skip_on_failure: bool = False) -> List[TestResult]:
        """
        Запуск полной пирамиды тестирования в правильном порядке
        """
        logger.info("🏗️ Starting Full Test Pyramid Execution...")
        
        # Создание директорий для результатов
        self._setup_result_directories()
        
        test_functions = [
            self.run_smoke_tests,      # Быстрая проверка работоспособности
            self.run_unit_tests,       # База пирамиды
            self.run_integration_tests, # Средний уровень
            self.run_e2e_tests,        # Вершина пирамиды
            self.run_performance_tests  # Специальные тесты
        ]
        
        for test_func in test_functions:
            try:
                result = test_func()
                
                # Проверка на критические ошибки
                if skip_on_failure and result.exit_code != 0:
                    logger.error(f"❌ {result.test_type} failed, stopping pyramid execution")
                    break
                    
            except Exception as e:
                logger.error(f"💥 Error executing {test_func.__name__}: {e}")
                error_result = TestResult(
                    test_type=test_func.__name__.replace("run_", "").replace("_", " ").title(),
                    passed=0,
                    failed=1,
                    skipped=0,
                    duration=0,
                    exit_code=1,
                    details={"error": str(e)}
                )
                self.results.append(error_result)
                
                if skip_on_failure:
                    break
        
        # Генерация финального отчета
        self.generate_pyramid_report()
        return self.results
    
    def _parse_pytest_output(self, output: str) -> tuple[int, int, int]:
        """Парсинг вывода pytest для извлечения результатов"""
        passed = failed = skipped = 0
        
        # Поиск строки с результатами
        for line in output.split('\n'):
            if 'passed' in line or 'failed' in line or 'error' in line:
                # Примеры: "15 passed, 2 failed, 1 skipped"
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        passed = int(part.split()[0])
                    elif 'failed' in part or 'error' in part:
                        failed = int(part.split()[0])
                    elif 'skipped' in part:
                        skipped = int(part.split()[0])
                break
        
        return passed, failed, skipped
    
    def _extract_coverage(self, coverage_file: str) -> float:
        """Извлечение процента покрытия из JSON файла"""
        try:
            coverage_path = self.project_root / coverage_file
            if coverage_path.exists():
                with open(coverage_path, 'r') as f:
                    data = json.load(f)
                    return data.get('totals', {}).get('percent_covered', 0.0)
        except Exception as e:
            logger.warning(f"Could not extract coverage from {coverage_file}: {e}")
        
        return 0.0
    
    def _log_test_result(self, result: TestResult):
        """Логирование результата теста"""
        status_emoji = "✅" if result.exit_code == 0 else "❌"
        logger.info(
            f"{status_emoji} {result.test_type}: "
            f"{result.passed} passed, {result.failed} failed, {result.skipped} skipped "
            f"({result.duration:.2f}s)"
            + (f", coverage: {result.coverage:.1f}%" if result.coverage > 0 else "")
        )
    
    def _setup_result_directories(self):
        """Создание директорий для результатов тестов"""
        directories = ['test-results', 'htmlcov', 'htmlcov/unit', 'htmlcov/integration']
        for directory in directories:
            (self.project_root / directory).mkdir(parents=True, exist_ok=True)
    
    def generate_pyramid_report(self):
        """Генерация финального отчета по пирамиде тестирования"""
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        # Подсчет общих метрик
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_tests = total_passed + total_failed + total_skipped
        
        # Средний coverage (для тех тестов, где он есть)
        coverage_results = [r for r in self.results if r.coverage > 0]
        avg_coverage = sum(r.coverage for r in coverage_results) / len(coverage_results) if coverage_results else 0
        
        report = f"""
# 🏗️ Test Pyramid Execution Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {total_duration:.2f} seconds

## 📊 Overall Summary
- **Total Tests**: {total_tests}
- **Passed**: {total_passed} ✅
- **Failed**: {total_failed} ❌
- **Skipped**: {total_skipped} ⏸️
- **Average Coverage**: {avg_coverage:.1f}%

## 📈 Test Pyramid Results

"""
        
        # Детали по каждому уровню
        for result in self.results:
            status = "✅ PASSED" if result.exit_code == 0 else "❌ FAILED"
            coverage_info = f" | Coverage: {result.coverage:.1f}%" if result.coverage > 0 else ""
            
            report += f"""### {result.test_type} {status}
- Tests: {result.passed + result.failed + result.skipped}
- Passed: {result.passed}
- Failed: {result.failed}  
- Skipped: {result.skipped}
- Duration: {result.duration:.2f}s{coverage_info}

"""
        
        # Рекомендации по исправлению
        if total_failed > 0:
            report += """## 🔧 Recommendations for Failed Tests

1. **Check test-results/*.json** for detailed failure information
2. **Review htmlcov/index.html** for coverage gaps
3. **Run individual test types** to isolate issues:
   ```bash
   pytest tests/unit/ -v --tb=long
   pytest tests/integration/ -v --tb=long  
   ```
4. **Check service dependencies** for integration test failures
5. **Verify test data and mocks** for E2E test issues

"""
        
        # Сохранение отчета
        report_path = self.project_root / "test-results" / "pyramid-report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Также создаем JSON отчет для машинной обработки
        json_report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "average_coverage": avg_coverage
            },
            "results": [
                {
                    "test_type": r.test_type,
                    "passed": r.passed,
                    "failed": r.failed,
                    "skipped": r.skipped,
                    "duration": r.duration,
                    "coverage": r.coverage,
                    "exit_code": r.exit_code
                }
                for r in self.results
            ]
        }
        
        json_report_path = self.project_root / "test-results" / "pyramid-report.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Test pyramid report saved to {report_path}")
        logger.info(f"📊 JSON report saved to {json_report_path}")
        
        print(report)

if __name__ == "__main__":
    """
    Запуск полной пирамиды тестирования
    
    Usage:
        python tests/test_pyramid_executor.py [--skip-on-failure]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Assistant MVP Test Pyramid Executor")
    parser.add_argument(
        "--skip-on-failure", 
        action="store_true",
        help="Stop pyramid execution on first test failure"
    )
    parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "e2e", "performance", "smoke", "all"],
        default="all",
        help="Type of tests to run"
    )
    
    args = parser.parse_args()
    
    executor = TestPyramidExecutor()
    
    if args.test_type == "all":
        results = executor.run_full_pyramid(skip_on_failure=args.skip_on_failure)
    elif args.test_type == "unit":
        results = [executor.run_unit_tests()]
    elif args.test_type == "integration":
        results = [executor.run_integration_tests()]
    elif args.test_type == "e2e":
        results = [executor.run_e2e_tests()]
    elif args.test_type == "performance":
        results = [executor.run_performance_tests()]
    elif args.test_type == "smoke":
        results = [executor.run_smoke_tests()]
    
    # Определение exit кода на основе результатов
    exit_code = 0 if all(r.exit_code == 0 for r in results) else 1
    sys.exit(exit_code) 