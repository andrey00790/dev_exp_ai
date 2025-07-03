"""
🧪 Advanced Security Engine Tests

Unit tests for the advanced security engine and API endpoints.
Phase 4B.2 - Advanced Intelligence Security Component Testing
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock

import pytest

from domain.monitoring.advanced_security_engine import (AdvancedSecurityEngine,
                                                        CodeSecurityScanner,
                                                        SecurityCategory,
                                                        SecurityReport,
                                                        SecurityVulnerability,
                                                        ThreatLevel,
                                                        VulnerabilityType,
                                                        get_security_engine)


class TestAdvancedSecurityEngine:
    """Test suite for AdvancedSecurityEngine"""

    @pytest.fixture
    def engine(self):
        """Create a test engine instance"""
        return AdvancedSecurityEngine()

    @pytest.fixture
    def sample_code_with_vulnerabilities(self):
        """Sample code containing security vulnerabilities"""
        return """
        def login(username, password):
            # SQL Injection vulnerability
            query = "SELECT * FROM users WHERE username = '" + username + "'"
            
            # Weak crypto vulnerability  
            import hashlib
            hashed = hashlib.md5(password.encode()).hexdigest()
            
            return query
        """

    @pytest.fixture
    def sample_system_config(self):
        """Sample system configuration with security issues"""
        return {
            "debug_mode": True,
            "admin_password": "admin",
            "encryption_enabled": False,
        }

    @pytest.mark.asyncio
    async def test_comprehensive_security_scan_basic(
        self, engine, sample_code_with_vulnerabilities, sample_system_config
    ):
        """Test basic comprehensive security scan"""
        scan_config = {
            "code_content": sample_code_with_vulnerabilities,
            "file_path": "test_file.py",
            "system_config": sample_system_config,
        }

        result = await engine.comprehensive_security_scan("test_target", scan_config)

        assert isinstance(result, SecurityReport)
        assert result.target == "test_target"
        assert len(result.vulnerabilities) > 0
        assert result.risk_score > 0
        assert len(result.recommendations) > 0
        assert result.scan_duration >= 0

    @pytest.mark.asyncio
    async def test_code_security_scanning(
        self, engine, sample_code_with_vulnerabilities
    ):
        """Test code security scanning functionality"""
        vulnerabilities = await engine.scan_code_security(
            sample_code_with_vulnerabilities, "test.py"
        )

        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) > 0

        # Verify vulnerability properties
        for vuln in vulnerabilities:
            assert isinstance(vuln, SecurityVulnerability)
            assert vuln.vulnerability_id is not None
            assert vuln.title != ""
            assert vuln.description != ""
            assert vuln.location != ""
            assert len(vuln.remediation) > 0
            assert 0 <= vuln.confidence <= 1

    @pytest.mark.asyncio
    async def test_configuration_security_scanning(self, engine, sample_system_config):
        """Test configuration security scanning"""
        vulnerabilities = await engine.scan_configuration_security(sample_system_config)

        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) >= 2  # Should find debug mode and weak password

        # Check for expected vulnerabilities
        titles = [v.title for v in vulnerabilities]
        assert any("Debug Mode" in title for title in titles)
        assert any("Password" in title for title in titles)

    @pytest.mark.asyncio
    async def test_quick_security_check(self, engine):
        """Test quick security check functionality"""
        result = await engine.quick_security_check("test_target", "basic")

        assert isinstance(result, dict)
        assert "target" in result
        assert "check_type" in result
        assert "issues_found" in result
        assert "risk_level" in result
        assert "scan_duration" in result
        assert "recommendations" in result
        assert "timestamp" in result

        assert result["target"] == "test_target"
        assert result["check_type"] == "basic"
        assert isinstance(result["issues_found"], int)
        assert result["risk_level"] in ["low", "medium", "high", "critical"]

    def test_risk_score_calculation(self, engine):
        """Test risk score calculation logic"""
        # Test with no vulnerabilities
        risk_score = engine._calculate_risk_score([])
        assert risk_score == 0.0

        # Test with mixed severity vulnerabilities
        vulnerabilities = [
            SecurityVulnerability(threat_level=ThreatLevel.CRITICAL),
            SecurityVulnerability(threat_level=ThreatLevel.HIGH),
            SecurityVulnerability(threat_level=ThreatLevel.MEDIUM),
        ]

        risk_score = engine._calculate_risk_score(vulnerabilities)
        assert 0 <= risk_score <= 10
        assert isinstance(risk_score, float)

    def test_security_recommendations_generation(self, engine):
        """Test security recommendations generation"""
        # Test with critical vulnerabilities
        critical_vulns = [
            SecurityVulnerability(threat_level=ThreatLevel.CRITICAL),
            SecurityVulnerability(threat_level=ThreatLevel.CRITICAL),
        ]

        recommendations = engine._generate_security_recommendations(critical_vulns)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("URGENT" in rec for rec in recommendations)

    def test_metrics_tracking(self, engine):
        """Test security metrics tracking"""
        initial_metrics = engine.metrics.copy()

        # Create mock report
        mock_report = SecurityReport(
            target="test",
            vulnerabilities=[
                SecurityVulnerability(threat_level=ThreatLevel.CRITICAL),
                SecurityVulnerability(threat_level=ThreatLevel.HIGH),
            ],
        )

        # Update metrics
        engine._update_metrics(mock_report)

        # Verify metrics were updated
        assert (
            engine.metrics["scans_performed"] == initial_metrics["scans_performed"] + 1
        )
        assert (
            engine.metrics["vulnerabilities_detected"]
            == initial_metrics["vulnerabilities_detected"] + 2
        )
        assert (
            engine.metrics["critical_issues"] == initial_metrics["critical_issues"] + 1
        )


class TestCodeSecurityScanner:
    """Test suite for CodeSecurityScanner"""

    @pytest.fixture
    def scanner(self):
        """Create a test scanner instance"""
        return CodeSecurityScanner()

    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, scanner):
        """Test SQL injection pattern detection"""
        vulnerable_code = """
        def get_user(user_id):
            query = "SELECT * FROM users WHERE id = " + str(user_id)
            return execute_query(query)
        """

        vulnerabilities = await scanner.scan_code(vulnerable_code, "test.py")

        sql_injection_vulns = [
            v
            for v in vulnerabilities
            if v.vulnerability_type == VulnerabilityType.SQL_INJECTION
        ]
        assert len(sql_injection_vulns) > 0

        vuln = sql_injection_vulns[0]
        assert vuln.threat_level == ThreatLevel.HIGH
        assert "SQL injection" in vuln.description
        assert len(vuln.remediation) > 0

    @pytest.mark.asyncio
    async def test_weak_crypto_detection(self, scanner):
        """Test weak cryptography detection"""
        vulnerable_code = """
        import hashlib
        
        def hash_password(password):
            return hashlib.md5(password.encode()).hexdigest()
        """

        vulnerabilities = await scanner.scan_code(vulnerable_code, "crypto.py")

        crypto_vulns = [
            v
            for v in vulnerabilities
            if v.vulnerability_type == VulnerabilityType.WEAK_CRYPTO
        ]
        assert len(crypto_vulns) > 0

        vuln = crypto_vulns[0]
        assert vuln.threat_level == ThreatLevel.MEDIUM
        assert "weak" in vuln.description.lower()

    @pytest.mark.asyncio
    async def test_clean_code_scanning(self, scanner):
        """Test scanning of clean code without vulnerabilities"""
        clean_code = """
        def safe_function():
            data = {"message": "Hello, World!"}
            return json.dumps(data)
        """

        vulnerabilities = await scanner.scan_code(clean_code, "clean.py")
        assert len(vulnerabilities) == 0


class TestGlobalEngineInstance:
    """Test suite for global engine instance management"""

    @pytest.mark.asyncio
    async def test_get_security_engine_singleton(self):
        """Test that get_security_engine returns the same instance"""
        engine1 = await get_security_engine()
        engine2 = await get_security_engine()

        assert engine1 is engine2
        assert isinstance(engine1, AdvancedSecurityEngine)

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine initialization"""
        engine = await get_security_engine()

        assert hasattr(engine, "metrics")
        assert hasattr(engine, "code_scanner")
        assert "scans_performed" in engine.metrics
        assert "vulnerabilities_detected" in engine.metrics
        assert "critical_issues" in engine.metrics


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_empty_code_scanning(self):
        """Test scanning empty code"""
        engine = AdvancedSecurityEngine()

        vulnerabilities = await engine.scan_code_security("", "empty.py")
        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) == 0

    @pytest.mark.asyncio
    async def test_empty_config_scanning(self):
        """Test scanning empty configuration"""
        engine = AdvancedSecurityEngine()

        vulnerabilities = await engine.scan_configuration_security({})
        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) == 0


class TestPerformance:
    """Test suite for performance characteristics"""

    @pytest.mark.asyncio
    async def test_scanning_performance(self):
        """Test scanning performance"""
        engine = AdvancedSecurityEngine()

        large_code = (
            """
        def function():
            query = "SELECT * FROM table WHERE id = " + str(user_input)
            return query
        """
            * 10
        )  # Create moderately sized code sample

        start_time = datetime.now()
        vulnerabilities = await engine.scan_code_security(large_code, "large_file.py")
        duration = (datetime.now() - start_time).total_seconds()

        assert duration < 2.0  # Should complete within 2 seconds
        assert isinstance(vulnerabilities, list)

    @pytest.mark.asyncio
    async def test_concurrent_scans(self):
        """Test concurrent scan handling"""
        engine = AdvancedSecurityEngine()

        code_sample = """
        def login(user, pass):
            query = "SELECT * FROM users WHERE name = '" + user + "'"
            return query
        """

        # Create multiple concurrent scan tasks
        tasks = [
            engine.scan_code_security(code_sample, f"file_{i}.py") for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(isinstance(result, list) for result in results)
        assert all(len(result) > 0 for result in results)  # Should find vulnerabilities
