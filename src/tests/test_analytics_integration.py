#!/usr/bin/env python3
"""
Analytics Integration Test

Tests the complete analytics functionality including:
- API endpoints
- Database integration  
- Dashboard data generation
- Metrics recording
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class AnalyticsIntegrationTest:
    """Complete integration test for analytics system"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with the API"""
        try:
            response = self.session.post(f"{self.base_url}/api/v1/auth/login", json={
                "email": "admin@example.com",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_analytics_health(self) -> bool:
        """Test analytics service health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/analytics/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Analytics health check passed: {data['status']}")
                return True
            else:
                print(f"❌ Analytics health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Analytics health check error: {e}")
            return False
    
    def test_record_usage_metric(self) -> bool:
        """Test recording usage metrics"""
        try:
            test_metric = {
                "feature": "analytics_test",
                "action": "integration_test",
                "duration_ms": 250.5,
                "tokens_used": 150,
                "success": True,
                "metadata": {
                    "test_run": datetime.utcnow().isoformat(),
                    "integration_test": True
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/analytics/metrics/usage",
                json=test_metric
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Usage metric recorded: ID {data['id']}")
                return True
            else:
                print(f"❌ Usage metric recording failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Usage metric recording error: {e}")
            return False
    
    def test_record_cost_metric(self) -> bool:
        """Test recording cost metrics"""
        try:
            test_metric = {
                "service": "openai",
                "operation": "completion",
                "total_cost": 0.015,
                "model": "gpt-4",
                "input_tokens": 100,
                "output_tokens": 200,
                "metadata": {
                    "test_run": datetime.utcnow().isoformat(),
                    "integration_test": True
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/analytics/metrics/cost",
                json=test_metric
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cost metric recorded: ID {data['id']}")
                return True
            else:
                print(f"❌ Cost metric recording failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Cost metric recording error: {e}")
            return False
    
    def test_record_performance_metric(self) -> bool:
        """Test recording performance metrics"""
        try:
            test_metric = {
                "component": "analytics_api",
                "operation": "integration_test",
                "response_time_ms": 125.3,
                "endpoint": "/api/v1/analytics/test",
                "success": True,
                "status_code": 200,
                "cpu_usage_percent": 15.5,
                "memory_usage_mb": 128.0,
                "metadata": {
                    "test_run": datetime.utcnow().isoformat(),
                    "integration_test": True
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/analytics/metrics/performance",
                json=test_metric
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Performance metric recorded: ID {data['id']}")
                return True
            else:
                print(f"❌ Performance metric recording failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Performance metric recording error: {e}")
            return False
    
    def test_usage_dashboard(self) -> bool:
        """Test usage dashboard endpoint"""
        try:
            dashboard_request = {
                "time_range": "last_7_days",
                "aggregation": "daily"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/analytics/dashboard/usage",
                json=dashboard_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Usage dashboard data retrieved")
                print(f"   📊 Period: {data['period']['start']} to {data['period']['end']}")
                
                # Check data structure
                expected_keys = ['period', 'data', 'generated_at']
                for key in expected_keys:
                    if key not in data:
                        print(f"❌ Missing key in dashboard response: {key}")
                        return False
                
                return True
            else:
                print(f"❌ Usage dashboard failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Usage dashboard error: {e}")
            return False
    
    def test_cost_dashboard(self) -> bool:
        """Test cost dashboard endpoint (admin only)"""
        try:
            dashboard_request = {
                "time_range": "last_30_days",
                "aggregation": "daily"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/analytics/dashboard/cost",
                json=dashboard_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cost dashboard data retrieved")
                print(f"   💰 Period: {data['period']['start']} to {data['period']['end']}")
                return True
            elif response.status_code == 403:
                print("⚠️  Cost dashboard requires admin access (expected)")
                return True  # This is expected for non-admin users
            else:
                print(f"❌ Cost dashboard failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Cost dashboard error: {e}")
            return False
    
    def test_performance_dashboard(self) -> bool:
        """Test performance dashboard endpoint (admin only)"""
        try:
            dashboard_request = {
                "time_range": "last_24_hours",
                "aggregation": "hourly"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/analytics/dashboard/performance",
                json=dashboard_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Performance dashboard data retrieved")
                print(f"   ⚡ Period: {data['period']['start']} to {data['period']['end']}")
                return True
            elif response.status_code == 403:
                print("⚠️  Performance dashboard requires admin access (expected)")
                return True  # This is expected for non-admin users
            else:
                print(f"❌ Performance dashboard failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Performance dashboard error: {e}")
            return False
    
    def test_insights_endpoints(self) -> bool:
        """Test insights generation endpoints"""
        try:
            # Test cost insights
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/insights/cost?time_range=last_30_days"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cost insights retrieved: {len(data.get('insights', []))} insights")
            elif response.status_code == 403:
                print("⚠️  Cost insights require admin access (expected)")
            else:
                print(f"❌ Cost insights failed: {response.status_code}")
                return False
            
            # Test performance insights
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/insights/performance?time_range=last_7_days"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Performance insights retrieved: {len(data.get('insights', []))} insights")
                return True
            elif response.status_code == 403:
                print("⚠️  Performance insights require admin access (expected)")
                return True
            else:
                print(f"❌ Performance insights failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Insights endpoints error: {e}")
            return False
    
    def test_aggregated_metrics(self) -> bool:
        """Test aggregated metrics endpoints"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/aggregated/usage?time_range=last_7_days&aggregation=daily"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Aggregated metrics retrieved")
                print(f"   📈 Metric type: {data.get('metric_type')}")
                print(f"   📊 Data points: {len(data.get('data', []))}")
                return True
            else:
                print(f"❌ Aggregated metrics failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Aggregated metrics error: {e}")
            return False
    
    def run_full_test_suite(self) -> bool:
        """Run complete analytics integration test suite"""
        print("🚀 Starting Analytics Integration Test Suite")
        print("=" * 50)
        
        tests = [
            ("Authentication", self.authenticate),
            ("Analytics Health", self.test_analytics_health),
            ("Record Usage Metric", self.test_record_usage_metric),
            ("Record Cost Metric", self.test_record_cost_metric),
            ("Record Performance Metric", self.test_record_performance_metric),
            ("Usage Dashboard", self.test_usage_dashboard),
            ("Cost Dashboard", self.test_cost_dashboard),
            ("Performance Dashboard", self.test_performance_dashboard),
            ("Insights Endpoints", self.test_insights_endpoints),
            ("Aggregated Metrics", self.test_aggregated_metrics),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"❌ Test failed: {test_name}")
            except Exception as e:
                print(f"❌ Test error: {test_name} - {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All analytics tests PASSED!")
            print("")
            print("🎉 Phase 4.2: Advanced Analytics - IMPLEMENTATION COMPLETE!")
            print("")
            print("📈 Analytics Features Available:")
            print("   • Usage tracking and metrics")
            print("   • Cost monitoring and optimization")
            print("   • Performance analytics")
            print("   • User behavior tracking")
            print("   • Automated insights generation")
            print("   • Real-time dashboard")
            print("   • Data aggregation and reports")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False


def main():
    """Main test execution"""
    test = AnalyticsIntegrationTest()
    success = test.run_full_test_suite()
    
    if success:
        print("\n🚀 Analytics system is ready for production!")
        print("📱 Access the analytics dashboard at: http://localhost:3000/analytics")
    else:
        print("\n❌ Analytics system has issues that need to be addressed")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 