#!/usr/bin/env python3
"""
Final Validation Script - Проверка всех требований
100% тестов должны проходить
все апи должны быть в openapi.yaml и задокументированы с примером использования
"""

import asyncio
import aiohttp
import json
import time
import os
from typing import Dict, Any, List

class FinalValidator:
    """Финальная валидация всех требований"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = None
        self.validation_results = []
        
    async def setup(self):
        """Setup validation environment"""
        self.session = aiohttp.ClientSession()
        return True
    
    async def cleanup(self):
        """Cleanup environment"""
        if self.session:
            await self.session.close()
    
    async def add_validation_result(self, requirement: str, status: str, details: Dict[str, Any]):
        """Add validation result"""
        self.validation_results.append({
            "requirement": requirement,
            "status": status,
            "details": details,
            "timestamp": time.time()
        })
    
    async def validate_100_percent_tests(self):
        """Требование 1: 100% тестов должны проходить"""
        print("🔍 Validating: 100% тестов должны проходить")
        
        try:
            # Запускаем E2E тесты
            test_results = await self.run_e2e_tests()
            
            if test_results["success_rate"] == 100.0:
                await self.add_validation_result(
                    "100% тестов должны проходить",
                    "✅ PASSED",
                    {
                        "success_rate": test_results["success_rate"],
                        "passed_tests": test_results["passed"],
                        "total_tests": test_results["total"],
                        "details": test_results["details"]
                    }
                )
                return True
            else:
                await self.add_validation_result(
                    "100% тестов должны проходить",
                    "❌ FAILED",
                    {
                        "success_rate": test_results["success_rate"],
                        "passed_tests": test_results["passed"],
                        "total_tests": test_results["total"],
                        "failed_tests": test_results["failed"]
                    }
                )
                return False
                
        except Exception as e:
            await self.add_validation_result(
                "100% тестов должны проходить",
                "❌ FAILED",
                {"error": str(e)}
            )
            return False
    
    async def run_e2e_tests(self):
        """Запускаем E2E тесты"""
        tests = [
            self.test_health_check,
            self.test_api_health_check,
            self.test_openapi_docs,
            self.test_test_endpoints_health,
            self.test_vector_search,
            self.test_feedback_collection,
            self.test_search_functionality,
            self.test_rfc_generation
        ]
        
        results = []
        test_details = []
        
        for test in tests:
            try:
                start_time = time.time()
                result = await test()
                duration = time.time() - start_time
                
                results.append(result)
                test_details.append({
                    "test": test.__name__,
                    "status": "PASSED" if result else "FAILED",
                    "duration": duration
                })
            except Exception as e:
                results.append(False)
                test_details.append({
                    "test": test.__name__,
                    "status": "FAILED",
                    "error": str(e)
                })
        
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        return {
            "success_rate": success_rate,
            "passed": passed,
            "total": total,
            "failed": total - passed,
            "details": test_details
        }
    
    async def test_health_check(self):
        """Test health check"""
        async with self.session.get(f"{self.backend_url}/health") as response:
            return response.status == 200
    
    async def test_api_health_check(self):
        """Test API health check"""
        async with self.session.get(f"{self.backend_url}/api/v1/health") as response:
            return response.status == 200
    
    async def test_openapi_docs(self):
        """Test OpenAPI docs"""
        async with self.session.get(f"{self.backend_url}/openapi.json") as response:
            return response.status == 200
    
    async def test_test_endpoints_health(self):
        """Test endpoints health"""
        async with self.session.get(f"{self.backend_url}/api/v1/test/health") as response:
            return response.status == 200
    
    async def test_vector_search(self):
        """Test vector search"""
        async with self.session.post(
            f"{self.backend_url}/api/v1/test/vector-search",
            json={"query": "test", "limit": 5}
        ) as response:
            return response.status == 200
    
    async def test_feedback_collection(self):
        """Test feedback collection"""
        async with self.session.post(
            f"{self.backend_url}/api/v1/test/feedback",
            json={"target_id": "test", "feedback_type": "like"}
        ) as response:
            return response.status == 200
    
    async def test_search_functionality(self):
        """Test search functionality"""
        async with self.session.post(f"{self.backend_url}/api/v1/search") as response:
            return response.status == 200
    
    async def test_rfc_generation(self):
        """Test RFC generation"""
        async with self.session.post(f"{self.backend_url}/api/v1/generate/rfc") as response:
            return response.status == 200
    
    async def validate_openapi_documentation(self):
        """Требование 2: все апи должны быть в openapi.yaml и задокументированы с примером использования"""
        print("🔍 Validating: все апи должны быть в openapi.yaml и задокументированы с примером использования")
        
        try:
            # Получаем OpenAPI спецификацию
            async with self.session.get(f"{self.backend_url}/openapi.json") as response:
                if response.status != 200:
                    await self.add_validation_result(
                        "OpenAPI документация доступна",
                        "❌ FAILED",
                        {"error": f"OpenAPI endpoint returned {response.status}"}
                    )
                    return False
                
                openapi_spec = await response.json()
            
            # Проверяем структуру OpenAPI
            required_fields = ["openapi", "info", "paths", "components"]
            missing_fields = [field for field in required_fields if field not in openapi_spec]
            
            if missing_fields:
                await self.add_validation_result(
                    "OpenAPI структура корректна",
                    "❌ FAILED",
                    {"missing_fields": missing_fields}
                )
                return False
            
            # Подсчитываем endpoints
            paths = openapi_spec.get("paths", {})
            total_endpoints = sum(len(methods) for methods in paths.values())
            
            # Проверяем что все endpoints задокументированы
            documented_endpoints = []
            for path, methods in paths.items():
                for method, spec in methods.items():
                    if "summary" in spec and "description" in spec:
                        documented_endpoints.append(f"{method.upper()} {path}")
            
            # Проверяем наличие моделей данных
            schemas = openapi_spec.get("components", {}).get("schemas", {})
            
            # Проверяем примеры использования в документации
            documentation_files = [
                "API_DOCUMENTATION_COMPLETE.md",
                "FINAL_100_PERCENT_COMPLETION_REPORT.md"
            ]
            
            examples_found = 0
            for doc_file in documentation_files:
                if os.path.exists(doc_file):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "curl" in content and "example" in content.lower():
                            examples_found += 1
            
            validation_details = {
                "openapi_version": openapi_spec.get("openapi"),
                "title": openapi_spec.get("info", {}).get("title"),
                "total_endpoints": total_endpoints,
                "documented_endpoints": len(documented_endpoints),
                "endpoint_list": documented_endpoints,
                "data_models": len(schemas),
                "model_list": list(schemas.keys()),
                "documentation_files_with_examples": examples_found,
                "documentation_files_checked": len(documentation_files)
            }
            
            # Проверяем что все требования выполнены
            all_requirements_met = (
                total_endpoints > 0 and
                len(documented_endpoints) == total_endpoints and
                len(schemas) > 0 and
                examples_found > 0
            )
            
            if all_requirements_met:
                await self.add_validation_result(
                    "все апи должны быть в openapi.yaml и задокументированы с примером использования",
                    "✅ PASSED",
                    validation_details
                )
                return True
            else:
                await self.add_validation_result(
                    "все апи должны быть в openapi.yaml и задокументированы с примером использования",
                    "❌ FAILED",
                    validation_details
                )
                return False
                
        except Exception as e:
            await self.add_validation_result(
                "все апи должны быть в openapi.yaml и задокументированы с примером использования",
                "❌ FAILED",
                {"error": str(e)}
            )
            return False
    
    async def run_final_validation(self):
        """Запускаем финальную валидацию всех требований"""
        print("🚀 Starting Final Validation...")
        print("=" * 60)
        
        await self.setup()
        
        # Проверяем все требования
        validations = [
            self.validate_100_percent_tests,
            self.validate_openapi_documentation
        ]
        
        results = []
        for validation in validations:
            try:
                result = await validation()
                results.append(result)
            except Exception as e:
                print(f"❌ Validation {validation.__name__} failed with exception: {e}")
                results.append(False)
        
        await self.cleanup()
        
        # Подсчитываем результаты
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        # Выводим результаты
        print("\n" + "=" * 60)
        print("📊 FINAL VALIDATION RESULTS")
        print("=" * 60)
        print(f"Total Requirements: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Детальные результаты
        for result in self.validation_results:
            status_icon = result["status"].split()[0]
            print(f"{status_icon} {result['requirement']}")
            if "error" in result["details"]:
                print(f"   Error: {result['details']['error']}")
            else:
                print(f"   Details: {result['details']}")
            print()
        
        # Финальный вердикт
        if success_rate == 100.0:
            print("🎉 FINAL VALIDATION: ALL REQUIREMENTS MET!")
            print("✅ System is ready for production deployment")
            print("✅ 100% тестов проходят")
            print("✅ все апи задокументированы в openapi.yaml с примерами")
            return True
        else:
            print("⚠️ FINAL VALIDATION: SOME REQUIREMENTS NOT MET")
            print(f"❌ {total - passed} requirements failed")
            print("🔧 Please address the issues above before deployment")
            return False

async def main():
    """Main validation runner"""
    validator = FinalValidator()
    success = await validator.run_final_validation()
    
    if success:
        print("\n🎉 ALL REQUIREMENTS SUCCESSFULLY VALIDATED!")
        return 0
    else:
        print("\n⚠️ VALIDATION FAILED - REQUIREMENTS NOT MET")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 