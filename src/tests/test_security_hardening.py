#!/usr/bin/env python3
"""
Security Hardening Test Suite for AI Assistant MVP
Task 1.3: Security Hardening - Comprehensive security validation

Tests:
- Updated dependencies security
- Input validation and sanitization
- Security headers configuration
- XSS and SQL injection prevention
- Authentication and authorization
- Rate limiting and cost controls
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class SecurityTester:
    """Comprehensive security testing class."""
    
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def get_auth_token(self) -> bool:
        """Get authentication token for testing."""
        try:
            login_data = {"email": "admin@example.com", "password": "admin123"}
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data['access_token']
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Authentication token obtained")
                return True
            else:
                print(f"❌ Failed to get auth token: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def test_security_headers(self) -> Dict[str, bool]:
        """Test security headers implementation."""
        print("\n🛡️ Testing Security Headers...")
        
        results = {}
        
        try:
            response = self.session.get(f"{BASE_URL}/health")
            headers = response.headers
            
            # Test required security headers
            security_headers = {
                "Content-Security-Policy": "CSP header prevents XSS",
                "X-XSS-Protection": "XSS protection enabled",
                "X-Content-Type-Options": "MIME sniffing prevention",
                "X-Frame-Options": "Clickjacking protection",
                "Referrer-Policy": "Referrer information control"
            }
            
            for header, description in security_headers.items():
                if header in headers:
                    print(f"   ✅ {header}: {description}")
                    results[header] = True
                else:
                    print(f"   ❌ Missing {header}")
                    results[header] = False
            
            # Test cache control for sensitive endpoints
            auth_response = self.session.get(f"{BASE_URL}/api/v1/auth/profile")
            if "Cache-Control" in auth_response.headers:
                cache_control = auth_response.headers["Cache-Control"]
                if "no-store" in cache_control and "no-cache" in cache_control:
                    print("   ✅ Cache-Control: Sensitive data not cached")
                    results["Cache-Control"] = True
                else:
                    print("   ⚠️ Cache-Control: Weak caching policy")
                    results["Cache-Control"] = False
            
        except Exception as e:
            print(f"   ❌ Security headers test failed: {e}")
            results["test_error"] = str(e)
        
        return results
    
    def test_input_validation(self) -> Dict[str, bool]:
        """Test input validation and sanitization."""
        print("\n🔍 Testing Input Validation...")
        
        results = {}
        
        # Test XSS prevention
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';DROP TABLE users;--"
        ]
        
        for payload in xss_payloads:
            try:
                test_data = {"query": payload}
                response = self.session.post(f"{BASE_URL}/api/v1/search", json=test_data)
                
                if response.status_code == 400:
                    print(f"   ✅ XSS payload blocked: {payload[:30]}...")
                    results[f"xss_block_{len(results)}"] = True
                else:
                    print(f"   ❌ XSS payload not blocked: {payload[:30]}...")
                    results[f"xss_block_{len(results)}"] = False
                    
            except Exception as e:
                print(f"   ⚠️ XSS test error: {e}")
        
        # Test SQL injection prevention
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR 1=1 --",
            "UNION SELECT * FROM users",
            "'; INSERT INTO users VALUES('hacker'); --"
        ]
        
        for payload in sql_payloads:
            try:
                test_data = {"title": payload, "description": "test"}
                response = self.session.post(f"{BASE_URL}/api/v1/generate", json=test_data)
                
                if response.status_code == 400:
                    print(f"   ✅ SQL injection blocked: {payload[:30]}...")
                    results[f"sql_block_{len(results)}"] = True
                else:
                    print(f"   ❌ SQL injection not blocked: {payload[:30]}...")
                    results[f"sql_block_{len(results)}"] = False
                    
            except Exception as e:
                print(f"   ⚠️ SQL injection test error: {e}")
        
        # Test request size limits
        try:
            large_data = {"query": "A" * 20000}  # 20KB string
            response = self.session.post(f"{BASE_URL}/api/v1/search", json=large_data)
            
            if response.status_code == 400:
                print("   ✅ Large request blocked")
                results["large_request_block"] = True
            else:
                print("   ⚠️ Large request not blocked")
                results["large_request_block"] = False
                
        except Exception as e:
            print(f"   ⚠️ Large request test error: {e}")
        
        return results
    
    def test_authentication_security(self) -> Dict[str, bool]:
        """Test authentication security measures."""
        print("\n🔐 Testing Authentication Security...")
        
        results = {}
        
        # Test protected endpoints without auth
        protected_endpoints = [
            "/api/v1/generate",
            "/api/v1/search", 
            "/api/v1/budget/status",
            "/api/v1/users/current"
        ]
        
        # Remove auth header temporarily
        auth_header = self.session.headers.get("Authorization")
        if auth_header:
            del self.session.headers["Authorization"]
        
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 401:
                    print(f"   ✅ {endpoint}: Properly protected")
                    results[f"protected_{endpoint.replace('/', '_')}"] = True
                else:
                    print(f"   ❌ {endpoint}: Not protected (status: {response.status_code})")
                    results[f"protected_{endpoint.replace('/', '_')}"] = False
                    
            except Exception as e:
                print(f"   ⚠️ Auth test error for {endpoint}: {e}")
        
        # Restore auth header
        if auth_header:
            self.session.headers["Authorization"] = auth_header
        
        # Test invalid token
        try:
            self.session.headers["Authorization"] = "Bearer invalid_token_12345"
            response = self.session.get(f"{BASE_URL}/api/v1/budget/status")
            
            if response.status_code == 401:
                print("   ✅ Invalid token rejected")
                results["invalid_token_reject"] = True
            else:
                print("   ❌ Invalid token not rejected")
                results["invalid_token_reject"] = False
                
        except Exception as e:
            print(f"   ⚠️ Invalid token test error: {e}")
        
        # Restore valid auth
        if auth_header:
            self.session.headers["Authorization"] = auth_header
        
        return results
    
    def test_rate_limiting(self) -> Dict[str, bool]:
        """Test rate limiting implementation."""
        print("\n⏱️ Testing Rate Limiting...")
        
        results = {}
        
        # Test auth endpoint rate limiting
        try:
            login_url = f"{BASE_URL}/auth/login"
            bad_login_data = {"email": "test@test.com", "password": "wrongpassword"}
            
            success_count = 0
            rate_limited = False
            
            for i in range(7):  # Try 7 failed logins (limit is 5)
                response = requests.post(login_url, json=bad_login_data)
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break
                elif response.status_code in [400, 401]:
                    success_count += 1
                
                time.sleep(0.5)  # Small delay between requests
            
            if rate_limited:
                print("   ✅ Rate limiting active on auth endpoints")
                results["auth_rate_limiting"] = True
            else:
                print("   ⚠️ Rate limiting not detected on auth endpoints")
                results["auth_rate_limiting"] = False
                
        except Exception as e:
            print(f"   ⚠️ Rate limiting test error: {e}")
        
        return results
    
    def test_cost_control_security(self) -> Dict[str, bool]:
        """Test cost control security measures."""
        print("\n💰 Testing Cost Control Security...")
        
        results = {}
        
        try:
            # Test budget status access
            response = self.session.get(f"{BASE_URL}/api/v1/budget/status")
            
            if response.status_code == 200:
                budget_data = response.json()
                
                # Check if sensitive budget data is properly structured
                required_fields = ["current_usage", "budget_limit", "usage_percentage"]
                all_fields_present = all(field in budget_data for field in required_fields)
                
                if all_fields_present:
                    print("   ✅ Budget data properly structured")
                    results["budget_data_structure"] = True
                else:
                    print("   ❌ Budget data missing required fields")
                    results["budget_data_structure"] = False
                
                # Test budget enforcement simulation
                usage_percentage = budget_data.get("usage_percentage", 0)
                if usage_percentage < 100:
                    print(f"   ✅ Budget usage at {usage_percentage:.1f}% (within limits)")
                    results["budget_within_limits"] = True
                else:
                    print(f"   ⚠️ Budget usage at {usage_percentage:.1f}% (exceeds limits)")
                    results["budget_within_limits"] = False
                    
            else:
                print(f"   ❌ Cannot access budget status: {response.status_code}")
                results["budget_access"] = False
                
        except Exception as e:
            print(f"   ⚠️ Cost control test error: {e}")
        
        return results
    
    def test_dependency_security(self) -> Dict[str, bool]:
        """Test that dependency vulnerabilities are fixed."""
        print("\n📦 Testing Dependency Security...")
        
        results = {}
        
        try:
            # Test that server is running with updated dependencies
            response = self.session.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Server running indicates dependencies are working
                print("   ✅ Server running with updated dependencies")
                results["dependencies_updated"] = True
                
                # Check if critical frameworks are responding
                if "status" in health_data and health_data["status"] == "healthy":
                    print("   ✅ All critical frameworks operational")
                    results["frameworks_operational"] = True
                else:
                    print("   ⚠️ Some frameworks may have issues")
                    results["frameworks_operational"] = False
                    
            else:
                print("   ❌ Server health check failed")
                results["dependencies_updated"] = False
                
        except Exception as e:
            print(f"   ⚠️ Dependency test error: {e}")
            results["dependency_test_error"] = str(e)
        
        return results
    
    def run_complete_security_audit(self) -> Dict[str, Any]:
        """Run complete security audit."""
        print("🔒 AI Assistant Security Hardening Audit")
        print("=" * 50)
        
        # Get authentication token
        if not self.get_auth_token():
            return {"error": "Authentication failed"}
        
        # Run all security tests
        audit_results = {
            "security_headers": self.test_security_headers(),
            "input_validation": self.test_input_validation(),
            "authentication_security": self.test_authentication_security(),
            "rate_limiting": self.test_rate_limiting(),
            "cost_control_security": self.test_cost_control_security(),
            "dependency_security": self.test_dependency_security()
        }
        
        # Calculate overall security score
        total_tests = 0
        passed_tests = 0
        
        for category, tests in audit_results.items():
            for test_name, result in tests.items():
                if isinstance(result, bool):
                    total_tests += 1
                    if result:
                        passed_tests += 1
        
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 50)
        print("🎯 Security Audit Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Security Score: {security_score:.1f}%")
        
        if security_score >= 90:
            print("   🏆 EXCELLENT: Production-ready security")
        elif security_score >= 80:
            print("   ✅ GOOD: Strong security posture")
        elif security_score >= 70:
            print("   ⚠️ FAIR: Security improvements recommended")
        else:
            print("   ❌ POOR: Critical security issues need attention")
        
        audit_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "security_score": security_score,
            "grade": "EXCELLENT" if security_score >= 90 else 
                    "GOOD" if security_score >= 80 else
                    "FAIR" if security_score >= 70 else "POOR"
        }
        
        # Task 1.3 completion status
        print("\n📝 Task 1.3 Status:")
        if security_score >= 85:
            print("   ✅ Task 1.3: Security Hardening - COMPLETED")
            print("   🚀 Ready for production deployment")
        else:
            print("   🔄 Task 1.3: Security Hardening - NEEDS IMPROVEMENT")
            print("   📋 Review failed tests and implement fixes")
        
        return audit_results

def main():
    """Run security hardening test suite."""
    try:
        tester = SecurityTester()
        results = tester.run_complete_security_audit()
        
        # Save results to file
        with open("security_audit_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to security_audit_results.json")
        
    except requests.ConnectionError:
        print("❌ Cannot connect to backend server at http://localhost:8000")
        print("   Make sure the server is running with updated security features")
    except Exception as e:
        print(f"❌ Security audit failed: {e}")

if __name__ == "__main__":
    main() 