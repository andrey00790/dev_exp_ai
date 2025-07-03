"""
🔒 Advanced Security Engine - Phase 4B.2

Enterprise-grade security intelligence engine for comprehensive
threat detection, vulnerability assessment, and security compliance.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityCategory(Enum):
    """Categories of security issues"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_PROTECTION = "data_protection"
    INPUT_VALIDATION = "input_validation"
    CRYPTO_SECURITY = "crypto_security"
    NETWORK_SECURITY = "network_security"


class VulnerabilityType(Enum):
    """Types of security vulnerabilities"""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    AUTH_BYPASS = "auth_bypass"
    WEAK_CRYPTO = "weak_crypto"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability"""

    vulnerability_id: str = field(default_factory=lambda: str(uuid4()))
    vulnerability_type: VulnerabilityType = VulnerabilityType.SECURITY_MISCONFIGURATION
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    category: SecurityCategory = SecurityCategory.AUTHENTICATION
    title: str = ""
    description: str = ""
    location: str = ""
    remediation: List[str] = field(default_factory=list)
    confidence: float = 0.8
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityReport:
    """Comprehensive security assessment report"""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    target: str = ""
    vulnerabilities: List[SecurityVulnerability] = field(default_factory=list)
    risk_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    scan_duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class CodeSecurityScanner:
    """Scans source code for security vulnerabilities"""

    def __init__(self):
        self.patterns = {
            VulnerabilityType.SQL_INJECTION: [
                {
                    "pattern": r"(SELECT|INSERT|UPDATE|DELETE).*\+.*",
                    "description": "Potential SQL injection via string concatenation",
                    "severity": ThreatLevel.HIGH,
                }
            ],
            VulnerabilityType.XSS: [
                {
                    "pattern": r"innerHTML\s*=.*\+",
                    "description": "Potential XSS via innerHTML manipulation",
                    "severity": ThreatLevel.MEDIUM,
                }
            ],
            VulnerabilityType.WEAK_CRYPTO: [
                {
                    "pattern": r"MD5|SHA1",
                    "description": "Use of weak cryptographic hash function",
                    "severity": ThreatLevel.MEDIUM,
                }
            ],
        }

    async def scan_code(
        self, code_content: str, file_path: str = ""
    ) -> List[SecurityVulnerability]:
        """Scan code content for security vulnerabilities"""
        vulnerabilities = []

        for vuln_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                matches = re.finditer(
                    pattern, code_content, re.IGNORECASE | re.MULTILINE
                )

                for match in matches:
                    line_number = code_content[: match.start()].count("\n") + 1

                    vulnerability = SecurityVulnerability(
                        vulnerability_type=vuln_type,
                        threat_level=pattern_info["severity"],
                        category=self._get_category_for_vulnerability(vuln_type),
                        title=f"{vuln_type.value.replace('_', ' ').title()} Detected",
                        description=pattern_info["description"],
                        location=(
                            f"{file_path}:line {line_number}"
                            if file_path
                            else f"line {line_number}"
                        ),
                        remediation=self._get_remediation_for_vulnerability(vuln_type),
                        confidence=0.8,
                    )
                    vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _get_category_for_vulnerability(
        self, vuln_type: VulnerabilityType
    ) -> SecurityCategory:
        """Map vulnerability type to security category"""
        mapping = {
            VulnerabilityType.SQL_INJECTION: SecurityCategory.INPUT_VALIDATION,
            VulnerabilityType.XSS: SecurityCategory.INPUT_VALIDATION,
            VulnerabilityType.AUTH_BYPASS: SecurityCategory.AUTHENTICATION,
            VulnerabilityType.WEAK_CRYPTO: SecurityCategory.CRYPTO_SECURITY,
        }
        return mapping.get(vuln_type, SecurityCategory.AUTHENTICATION)

    def _get_remediation_for_vulnerability(
        self, vuln_type: VulnerabilityType
    ) -> List[str]:
        """Get remediation steps for vulnerability type"""
        remediation_map = {
            VulnerabilityType.SQL_INJECTION: [
                "Use parameterized queries or prepared statements",
                "Implement input validation and sanitization",
            ],
            VulnerabilityType.XSS: [
                "Implement output encoding/escaping",
                "Use Content Security Policy (CSP) headers",
            ],
            VulnerabilityType.WEAK_CRYPTO: [
                "Use strong cryptographic algorithms (AES-256, SHA-256+)",
                "Implement proper key management",
            ],
            VulnerabilityType.AUTH_BYPASS: [
                "Implement proper authentication mechanisms",
                "Use strong password policies",
            ],
        }
        return remediation_map.get(vuln_type, ["Conduct security review"])


class AdvancedSecurityEngine:
    """Advanced Security Engine for comprehensive security analysis"""

    def __init__(self):
        self.code_scanner = CodeSecurityScanner()
        self.metrics = {
            "scans_performed": 0,
            "vulnerabilities_detected": 0,
            "critical_issues": 0,
        }

    async def comprehensive_security_scan(
        self, target: str, scan_config: Dict[str, Any]
    ) -> SecurityReport:
        """Perform comprehensive security assessment"""
        scan_start = datetime.now()

        logger.info(f"🔒 Starting security scan for: {target}")

        report = SecurityReport(target=target)
        all_vulnerabilities = []

        # Code security scan
        if "code_content" in scan_config:
            code_vulns = await self.scan_code_security(
                scan_config["code_content"], scan_config.get("file_path", target)
            )
            all_vulnerabilities.extend(code_vulns)

        # Configuration security scan
        if "system_config" in scan_config:
            config_vulns = await self.scan_configuration_security(
                scan_config["system_config"]
            )
            all_vulnerabilities.extend(config_vulns)

        report.vulnerabilities = all_vulnerabilities
        report.risk_score = self._calculate_risk_score(all_vulnerabilities)
        report.recommendations = self._generate_security_recommendations(
            all_vulnerabilities
        )

        scan_duration = (datetime.now() - scan_start).total_seconds()
        report.scan_duration = scan_duration

        self._update_metrics(report)

        logger.info(
            f"✅ Security scan completed: {len(all_vulnerabilities)} vulnerabilities found"
        )
        return report

    async def scan_code_security(
        self, code_content: str, file_path: str = ""
    ) -> List[SecurityVulnerability]:
        """Scan source code for security vulnerabilities"""
        return await self.code_scanner.scan_code(code_content, file_path)

    async def scan_configuration_security(
        self, system_config: Dict[str, Any]
    ) -> List[SecurityVulnerability]:
        """Scan system configuration for security issues"""
        vulnerabilities = []

        # Check for debug mode in production
        if system_config.get("debug_mode", False):
            vulnerabilities.append(
                SecurityVulnerability(
                    vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                    threat_level=ThreatLevel.HIGH,
                    category=SecurityCategory.AUTHENTICATION,
                    title="Debug Mode Enabled in Production",
                    description="Debug mode exposes sensitive information",
                    location="system_config",
                    remediation=[
                        "Disable debug mode in production environments",
                        "Use environment-specific configuration",
                    ],
                    confidence=0.95,
                )
            )

        # Check for default credentials
        default_passwords = ["admin", "password", "123456"]
        admin_password = system_config.get("admin_password", "")
        if admin_password.lower() in default_passwords:
            vulnerabilities.append(
                SecurityVulnerability(
                    vulnerability_type=VulnerabilityType.AUTH_BYPASS,
                    threat_level=ThreatLevel.CRITICAL,
                    category=SecurityCategory.AUTHENTICATION,
                    title="Default/Weak Admin Password",
                    description="System is using default or weak admin password",
                    location="system_config",
                    remediation=[
                        "Change default passwords immediately",
                        "Implement strong password policy",
                    ],
                    confidence=0.98,
                )
            )

        return vulnerabilities

    def _calculate_risk_score(
        self, vulnerabilities: List[SecurityVulnerability]
    ) -> float:
        """Calculate overall risk score based on vulnerabilities"""
        if not vulnerabilities:
            return 0.0

        severity_weights = {
            ThreatLevel.CRITICAL: 10,
            ThreatLevel.HIGH: 7,
            ThreatLevel.MEDIUM: 4,
            ThreatLevel.LOW: 2,
            ThreatLevel.INFO: 1,
        }

        total_score = sum(
            severity_weights.get(v.threat_level, 1) for v in vulnerabilities
        )
        max_possible = len(vulnerabilities) * 10

        return round((total_score / max_possible) * 10, 2) if max_possible > 0 else 0.0

    def _generate_security_recommendations(
        self, vulnerabilities: List[SecurityVulnerability]
    ) -> List[str]:
        """Generate high-level security recommendations"""
        recommendations = []

        critical_count = len(
            [v for v in vulnerabilities if v.threat_level == ThreatLevel.CRITICAL]
        )
        high_count = len(
            [v for v in vulnerabilities if v.threat_level == ThreatLevel.HIGH]
        )

        if critical_count > 0:
            recommendations.append(
                f"🚨 URGENT: Address {critical_count} critical security vulnerabilities immediately"
            )

        if high_count > 0:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: Remediate {high_count} high-severity security issues"
            )

        recommendations.extend(
            [
                "🔐 Strengthen authentication mechanisms",
                "🛡️ Implement input validation",
                "🔍 Schedule regular security assessments",
            ]
        )

        return recommendations[:5]

    def _update_metrics(self, report: SecurityReport):
        """Update security engine metrics"""
        self.metrics["scans_performed"] += 1
        self.metrics["vulnerabilities_detected"] += len(report.vulnerabilities)

        critical_count = len(
            [
                v
                for v in report.vulnerabilities
                if v.threat_level == ThreatLevel.CRITICAL
            ]
        )
        self.metrics["critical_issues"] += critical_count

    async def quick_security_check(
        self, target: str, check_type: str = "basic"
    ) -> Dict[str, Any]:
        """Perform quick security check"""
        start_time = datetime.now()

        # Mock quick security check
        if check_type == "basic":
            issues_found = 2
            risk_level = "medium"
        else:
            issues_found = 1
            risk_level = "low"

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "target": target,
            "check_type": check_type,
            "issues_found": issues_found,
            "risk_level": risk_level,
            "scan_duration": duration,
            "recommendations": [
                "Review authentication mechanisms",
                "Update security headers",
            ][:issues_found],
            "timestamp": datetime.now().isoformat(),
        }

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        return {
            "engine_status": "active",
            "metrics": self.metrics,
            "last_updated": datetime.now().isoformat(),
        }


# Global instance
_security_engine_instance: Optional[AdvancedSecurityEngine] = None


async def get_security_engine() -> AdvancedSecurityEngine:
    """Get global security engine instance"""
    global _security_engine_instance
    if _security_engine_instance is None:
        _security_engine_instance = AdvancedSecurityEngine()
    return _security_engine_instance
