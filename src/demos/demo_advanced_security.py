"""
🔒 Advanced Security Engine Demo

Comprehensive demonstration of enterprise-grade security intelligence.
Phase 4B.2 - Advanced Intelligence Security Component Demo
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from domain.monitoring.advanced_security_engine import (
    get_security_engine,
    ThreatLevel,
    VulnerabilityType
)

class AdvancedSecurityDemo:
    """Demo class for showcasing advanced security capabilities"""
    
    def __init__(self):
        self.engine = None
        self.demo_results = []
    
    async def setup(self):
        """Initialize the security engine"""
        print("🔒 Initializing Advanced Security Engine...")
        self.engine = await get_security_engine()
        print("✅ Security engine initialized successfully!")
        print()
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        await self.setup()
        
        print("=" * 80)
        print("🔒 ADVANCED SECURITY ENGINE - COMPREHENSIVE DEMO")
        print("=" * 80)
        print()
        
        # Core security functionality demos
        await self.demo_code_security_scanning()
        await self.demo_configuration_security_scanning() 
        await self.demo_comprehensive_security_scan()
        await self.demo_quick_security_checks()
        await self.demo_security_metrics_tracking()
        
        # Summary
        await self.show_demo_summary()
    
    async def demo_code_security_scanning(self):
        """Demonstrate code security vulnerability scanning"""
        print("🔍 CODE SECURITY SCANNING DEMO")
        print("-" * 50)
        
        # Sample vulnerable code
        vulnerable_code = '''
        def authenticate_user(username, password):
            # SQL Injection vulnerability
            query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
            
            # Weak cryptography vulnerability
            import hashlib
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            return execute_query(query)
        '''
        
        print("Sample Code Analysis:")
        print("  • Python authentication function")
        print("  • Contains multiple security vulnerabilities")
        print("  • Testing pattern-based detection")
        print()
        
        print("🔒 Scanning code for security vulnerabilities...")
        start_time = time.time()
        
        vulnerabilities = await self.engine.scan_code_security(vulnerable_code, "auth.py")
        
        scan_time = (time.time() - start_time) * 1000
        
        print("✅ Code Scan Results:")
        print(f"  • Vulnerabilities Found: {len(vulnerabilities)}")
        print(f"  • Scan Time: {scan_time:.1f}ms")
        print()
        
        if vulnerabilities:
            print("🚨 Detected Vulnerabilities:")
            for i, vuln in enumerate(vulnerabilities, 1):
                threat_icon = self._get_threat_icon(vuln.threat_level)
                print(f"  {threat_icon} {i}. {vuln.title}")
                print(f"      Type: {vuln.vulnerability_type.value}")
                print(f"      Severity: {vuln.threat_level.value}")
                print(f"      Location: {vuln.location}")
                print(f"      Description: {vuln.description}")
                
                if vuln.remediation:
                    print(f"      💡 Remediation:")
                    for j, remedy in enumerate(vuln.remediation[:2], 1):
                        print(f"         {j}. {remedy}")
                print()
        
        self.demo_results.append({
            'type': 'code_scanning',
            'vulnerabilities_found': len(vulnerabilities),
            'scan_time_ms': scan_time
        })
    
    async def demo_configuration_security_scanning(self):
        """Demonstrate configuration security scanning"""
        print("⚙️ CONFIGURATION SECURITY SCANNING DEMO")
        print("-" * 50)
        
        # Sample insecure configuration
        insecure_config = {
            'debug_mode': True,
            'admin_password': 'admin',
            'encryption_enabled': False,
            'auth_enabled': True
        }
        
        print("Configuration Analysis:")
        print("  • Production system configuration")
        print("  • Checking for security misconfigurations")
        print()
        
        print("🔒 Scanning configuration for security issues...")
        start_time = time.time()
        
        vulnerabilities = await self.engine.scan_configuration_security(insecure_config)
        
        scan_time = (time.time() - start_time) * 1000
        
        print("✅ Configuration Scan Results:")
        print(f"  • Security Issues Found: {len(vulnerabilities)}")
        print(f"  • Scan Time: {scan_time:.1f}ms")
        print()
        
        if vulnerabilities:
            print("⚠️ Configuration Issues:")
            for i, vuln in enumerate(vulnerabilities, 1):
                threat_icon = self._get_threat_icon(vuln.threat_level)
                print(f"  {threat_icon} {i}. {vuln.title}")
                print(f"      Severity: {vuln.threat_level.value}")
                print(f"      Issue: {vuln.description}")
                print(f"      Confidence: {vuln.confidence:.1%}")
                print()
    
    async def demo_comprehensive_security_scan(self):
        """Demonstrate comprehensive security assessment"""
        print("🛡️ COMPREHENSIVE SECURITY ASSESSMENT DEMO")
        print("-" * 50)
        
        # Combined scan configuration
        scan_config = {
            'code_content': '''
            def process_payment(user_id, amount):
                # Vulnerable code
                query = "UPDATE accounts SET balance = balance - " + str(amount) + " WHERE id = " + str(user_id)
                return execute(query)
            ''',
            'file_path': 'payment.py',
            'system_config': {
                'debug_mode': True,
                'admin_password': '123456'
            }
        }
        
        print("Comprehensive Security Assessment:")
        print("  • Code vulnerability analysis")
        print("  • System configuration review")
        print("  • Risk scoring and prioritization")
        print()
        
        print("🔒 Performing comprehensive security scan...")
        start_time = time.time()
        
        report = await self.engine.comprehensive_security_scan("payment_system", scan_config)
        
        scan_time = (time.time() - start_time) * 1000
        
        print("✅ Comprehensive Scan Results:")
        print(f"  • Target: {report.target}")
        print(f"  • Total Vulnerabilities: {len(report.vulnerabilities)}")
        print(f"  • Risk Score: {report.risk_score}/10")
        print(f"  • Scan Duration: {scan_time:.1f}ms")
        print()
        
        # Risk assessment
        risk_level = self._get_risk_level(report.risk_score)
        risk_icon = self._get_risk_icon(risk_level)
        print(f"🎯 Risk Assessment: {risk_icon} {risk_level.upper()}")
        print()
        
        # Top recommendations
        if report.recommendations:
            print("🚨 Priority Recommendations:")
            for i, recommendation in enumerate(report.recommendations[:3], 1):
                print(f"  {i}. {recommendation}")
            print()
    
    async def demo_quick_security_checks(self):
        """Demonstrate quick security check functionality"""
        print("⚡ QUICK SECURITY CHECKS DEMO")
        print("-" * 50)
        
        targets = [
            ('web_application', 'basic'),
            ('api_service', 'standard'),
            ('database_server', 'basic')
        ]
        
        print("Quick Security Assessment Results:\n")
        
        for target, check_type in targets:
            print(f"🎯 Target: {target} (check type: {check_type})")
            
            start_time = time.time()
            result = await self.engine.quick_security_check(target, check_type)
            check_time = (time.time() - start_time) * 1000
            
            risk_icon = self._get_risk_icon(result['risk_level'])
            
            print(f"   {risk_icon} Risk Level: {result['risk_level']}")
            print(f"   🔍 Issues Found: {result['issues_found']}")
            print(f"   ⏱️ Check Time: {check_time:.1f}ms")
            
            if result['recommendations']:
                print(f"   💡 Quick Recommendations:")
                for rec in result['recommendations'][:2]:
                    print(f"      • {rec}")
            print()
    
    async def demo_security_metrics_tracking(self):
        """Demonstrate security metrics and monitoring"""
        print("📊 SECURITY METRICS & MONITORING DEMO")
        print("-" * 50)
        
        # Get current metrics
        metrics = self.engine.get_security_metrics()
        
        print("Security Engine Status:")
        print(f"  • Engine Status: {metrics['engine_status']}")
        print(f"  • Scans Performed: {metrics['metrics']['scans_performed']}")
        print(f"  • Vulnerabilities Detected: {metrics['metrics']['vulnerabilities_detected']}")
        print(f"  • Critical Issues: {metrics['metrics']['critical_issues']}")
        print()
        
        # Calculate security posture
        scans = metrics['metrics']['scans_performed']
        critical_issues = metrics['metrics']['critical_issues']
        
        if scans == 0:
            posture = "🟡 Ready for Assessment"
        elif critical_issues == 0:
            posture = "🟢 Good Security Posture"
        elif critical_issues <= 2:
            posture = "🟡 Needs Attention"
        else:
            posture = "🔴 High Risk - Immediate Action Required"
        
        print(f"Security Posture: {posture}")
        print()
    
    async def show_demo_summary(self):
        """Show comprehensive demo summary"""
        print("=" * 80)
        print("📊 DEMO SUMMARY")
        print("=" * 80)
        
        # Engine status after demo
        metrics = self.engine.get_security_metrics()
        
        print("Security Engine Performance:")
        print(f"  • Total Scans During Demo: {metrics['metrics']['scans_performed']}")
        print(f"  • Vulnerabilities Detected: {metrics['metrics']['vulnerabilities_detected']}")
        print(f"  • Critical Issues Found: {metrics['metrics']['critical_issues']}")
        print()
        
        print("Key Capabilities Demonstrated:")
        print("  ✅ Code security vulnerability scanning")
        print("  ✅ Configuration security assessment")
        print("  ✅ Comprehensive security reporting")
        print("  ✅ Quick security checks for rapid assessment")
        print("  ✅ Real-time security metrics tracking")
        print()
        
        print("Security Intelligence Features:")
        print("  🔒 Enterprise-grade vulnerability detection")
        print("  🛡️ Multi-layer security assessment")
        print("  📊 Risk scoring and prioritization")
        print("  🚨 Real-time threat level analysis")
        print("  💡 Automated remediation recommendations")
        print()
        
        print("Phase 4B.2 Status:")
        print("  🎯 Advanced Security Engine: IMPLEMENTED")
        print("  🔄 Additional security features: IN DEVELOPMENT")
        print()
        
        print("✨ Advanced Security Engine Demo Completed Successfully!")
        print("=" * 80)
    
    # Helper methods
    def _get_threat_icon(self, threat_level: ThreatLevel) -> str:
        """Get emoji icon for threat level"""
        icons = {
            ThreatLevel.CRITICAL: "🚨",
            ThreatLevel.HIGH: "⚠️",
            ThreatLevel.MEDIUM: "🟡",
            ThreatLevel.LOW: "🔵",
            ThreatLevel.INFO: "ℹ️"
        }
        return icons.get(threat_level, "❓")
    
    def _get_risk_icon(self, risk_level: str) -> str:
        """Get emoji icon for risk level"""
        icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        return icons.get(risk_level, '❓')
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 8.0:
            return 'critical'
        elif risk_score >= 6.0:
            return 'high'
        elif risk_score >= 4.0:
            return 'medium'
        else:
            return 'low'

async def main():
    """Run the comprehensive advanced security demo"""
    demo = AdvancedSecurityDemo()
    
    try:
        await demo.run_all_demos()
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    else:
        print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    print("Starting Advanced Security Engine Demo...")
    print("Press Ctrl+C to interrupt at any time.\n")
    
    asyncio.run(main())
