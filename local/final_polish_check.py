#!/usr/bin/env python3
"""
Final Polish Check Script
Comprehensive system health check and validation
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ColorOutput:
    """Console color output helper"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

    @classmethod
    def success(cls, message: str) -> None:
        print(f"{cls.GREEN}✅ {message}{cls.NC}")

    @classmethod
    def error(cls, message: str) -> None:
        print(f"{cls.RED}❌ {message}{cls.NC}")

    @classmethod
    def warning(cls, message: str) -> None:
        print(f"{cls.YELLOW}⚠️  {message}{cls.NC}")

    @classmethod
    def info(cls, message: str) -> None:
        print(f"{cls.BLUE}ℹ️  {message}{cls.NC}")

    @classmethod
    def header(cls, message: str) -> None:
        print(f"\n{cls.CYAN}🔍 {message}{cls.NC}")


class SystemChecker:
    """System health checker"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            'total_checks': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'checks': []
        }
    
    def run_command(self, cmd: str, capture_output: bool = True) -> Tuple[bool, str]:
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    def check_file_exists(self, file_path: str, name: str) -> bool:
        """Check if file exists"""
        self.results['total_checks'] += 1
        path = self.project_root / file_path
        
        if path.exists():
            ColorOutput.success(f"{name} exists: {file_path}")
            self.results['passed'] += 1
            self.results['checks'].append({
                'name': name,
                'status': 'passed',
                'path': file_path
            })
            return True
        else:
            ColorOutput.error(f"{name} missing: {file_path}")
            self.results['failed'] += 1
            self.results['checks'].append({
                'name': name,
                'status': 'failed',
                'path': file_path
            })
            return False
    
    def check_directory_exists(self, dir_path: str, name: str) -> bool:
        """Check if directory exists"""
        self.results['total_checks'] += 1
        path = self.project_root / dir_path
        
        if path.exists() and path.is_dir():
            ColorOutput.success(f"{name} directory exists: {dir_path}")
            self.results['passed'] += 1
            self.results['checks'].append({
                'name': name,
                'status': 'passed',
                'path': dir_path
            })
            return True
        else:
            ColorOutput.error(f"{name} directory missing: {dir_path}")
            self.results['failed'] += 1
            self.results['checks'].append({
                'name': name,
                'status': 'failed',
                'path': dir_path
            })
            return False
    
    def check_docker_compose_syntax(self) -> bool:
        """Check Docker Compose syntax"""
        ColorOutput.header("Checking Docker Compose syntax")
        self.results['total_checks'] += 1
        
        success, output = self.run_command("docker compose config")
        if success:
            ColorOutput.success("Docker Compose syntax is valid")
            self.results['passed'] += 1
            self.results['checks'].append({
                'name': 'Docker Compose Syntax',
                'status': 'passed',
                'details': 'Valid YAML syntax'
            })
            return True
        else:
            ColorOutput.error(f"Docker Compose syntax error: {output}")
            self.results['failed'] += 1
            self.results['checks'].append({
                'name': 'Docker Compose Syntax',
                'status': 'failed',
                'details': output
            })
            return False
    
    def check_makefile_syntax(self) -> bool:
        """Check Makefile syntax"""
        ColorOutput.header("Checking Makefile syntax")
        self.results['total_checks'] += 1
        
        success, output = self.run_command("make -n help")
        if success:
            ColorOutput.success("Makefile syntax is valid")
            self.results['passed'] += 1
            self.results['checks'].append({
                'name': 'Makefile Syntax',
                'status': 'passed',
                'details': 'Valid Makefile syntax'
            })
            return True
        else:
            ColorOutput.error(f"Makefile syntax error: {output}")
            self.results['failed'] += 1
            self.results['checks'].append({
                'name': 'Makefile Syntax',
                'status': 'failed',
                'details': output
            })
            return False
    
    def check_python_syntax(self) -> bool:
        """Check Python syntax of key files"""
        ColorOutput.header("Checking Python syntax")
        
        python_files = [
            'main.py',
            'app/main.py',
            'local/bootstrap_fetcher.py',
            'tests/e2e/test_basic_e2e.py'
        ]
        
        all_passed = True
        for file_path in python_files:
            self.results['total_checks'] += 1
            success, output = self.run_command(f"python -m py_compile {file_path}")
            
            if success:
                ColorOutput.success(f"Python syntax valid: {file_path}")
                self.results['passed'] += 1
                self.results['checks'].append({
                    'name': f'Python Syntax - {file_path}',
                    'status': 'passed',
                    'path': file_path
                })
            else:
                ColorOutput.error(f"Python syntax error in {file_path}: {output}")
                self.results['failed'] += 1
                self.results['checks'].append({
                    'name': f'Python Syntax - {file_path}',
                    'status': 'failed',
                    'path': file_path,
                    'details': output
                })
                all_passed = False
        
        return all_passed
    
    def check_requirements_files(self) -> bool:
        """Check requirements files"""
        ColorOutput.header("Checking requirements files")
        
        requirements_files = [
            'requirements.txt',
            'config/environments/requirements-prod.txt',
            'config/environments/requirements-ingestion.txt'
        ]
        
        all_passed = True
        for file_path in requirements_files:
            if not self.check_file_exists(file_path, f"Requirements file - {file_path}"):
                all_passed = False
        
        return all_passed
    
    def check_docker_files(self) -> bool:
        """Check Docker files"""
        ColorOutput.header("Checking Docker files")
        
        docker_files = [
            'docker-compose.yml',
            'deployment/docker/Dockerfile',
            'deployment/docker/Dockerfile.bootstrap',
            'deployment/docker/Dockerfile.playwright',
            'nginx/nginx-load-test.conf'
        ]
        
        all_passed = True
        for file_path in docker_files:
            if not self.check_file_exists(file_path, f"Docker file - {file_path}"):
                all_passed = False
        
        return all_passed
    
    def check_test_files(self) -> bool:
        """Check test files"""
        ColorOutput.header("Checking test files")
        
        test_files = [
            'tests/e2e/__init__.py',
            'tests/e2e/test_basic_e2e.py',
            'tests/e2e/conftest.py',
            'tests/e2e/basic.spec.ts',
            'tests/bootstrap/test_bootstrap_integration.py',
            'tests/performance/locustfile.py'
        ]
        
        all_passed = True
        for file_path in test_files:
            if not self.check_file_exists(file_path, f"Test file - {file_path}"):
                all_passed = False
        
        return all_passed
    
    def check_data_directories(self) -> bool:
        """Check data directories"""
        ColorOutput.header("Checking data directories")
        
        data_dirs = [
            'data',
            'data/postgres',
            'data/qdrant', 
            'data/redis',
            'data/e2e',
            'data/load',
            'logs'
        ]
        
        all_passed = True
        for dir_path in data_dirs:
            if not self.check_directory_exists(dir_path, f"Data directory - {dir_path}"):
                all_passed = False
        
        return all_passed
    
    def check_configuration_files(self) -> bool:
        """Check configuration files"""
        ColorOutput.header("Checking configuration files")
        
        config_files = [
            'local/local_bootstrap_config.yml',
            'local/resource_config.yml',
            'config/datasources.yaml',
            'playwright.config.ts',
            'alembic.ini'
        ]
        
        all_passed = True
        for file_path in config_files:
            if not self.check_file_exists(file_path, f"Config file - {file_path}"):
                all_passed = False
        
        return all_passed
    
    def check_documentation_files(self) -> bool:
        """Check documentation files"""
        ColorOutput.header("Checking documentation files")
        
        doc_files = [
            'README.md',
            'DOCKER_COMPOSE_UNIFIED_REPORT.md',
            'QUICK_START_DOCKER.md',
            'docs/requirements/FUNCTIONAL_NON_FUNCTIONAL_REQUIREMENTS.md',
            'docs/requirements/TESTING_REQUIREMENTS.md'
        ]
        
        all_passed = True
        for file_path in doc_files:
            if not self.check_file_exists(file_path, f"Documentation - {file_path}"):
                all_passed = False
        
        return all_passed
    
    def run_all_checks(self) -> Dict:
        """Run all system checks"""
        print("🔍 AI Assistant - Final Polish System Check")
        print("=" * 60)
        
        # Core infrastructure checks
        self.check_docker_compose_syntax()
        self.check_makefile_syntax()
        self.check_python_syntax()
        
        # File existence checks
        self.check_requirements_files()
        self.check_docker_files()
        self.check_test_files()
        self.check_data_directories()
        self.check_configuration_files()
        self.check_documentation_files()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 FINAL SYSTEM CHECK SUMMARY")
        print("=" * 60)
        
        total = self.results['total_checks']
        passed = self.results['passed']
        failed = self.results['failed']
        warnings = self.results['warnings']
        
        ColorOutput.info(f"Total checks: {total}")
        ColorOutput.success(f"Passed: {passed}")
        
        if failed > 0:
            ColorOutput.error(f"Failed: {failed}")
        
        if warnings > 0:
            ColorOutput.warning(f"Warnings: {warnings}")
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        if success_rate >= 95:
            ColorOutput.success(f"Success rate: {success_rate:.1f}% - EXCELLENT! 🎉")
        elif success_rate >= 85:
            ColorOutput.warning(f"Success rate: {success_rate:.1f}% - GOOD")
        else:
            ColorOutput.error(f"Success rate: {success_rate:.1f}% - NEEDS IMPROVEMENT")
        
        # Save results
        results_file = self.project_root / 'logs' / 'final_polish_check_results.json'
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        ColorOutput.info(f"Detailed results saved to: {results_file}")
        
        return self.results


def main():
    """Main function"""
    try:
        checker = SystemChecker()
        results = checker.run_all_checks()
        
        # Exit with appropriate code
        if results['failed'] == 0:
            print("\n🎉 System is ready for production!")
            sys.exit(0)
        else:
            print("\n⚠️  System needs attention before production deployment")
            sys.exit(1)
            
    except KeyboardInterrupt:
        ColorOutput.warning("Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        ColorOutput.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 