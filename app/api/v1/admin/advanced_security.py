"""
🔒 Advanced Security API - Phase 4B.2

FastAPI endpoints for enterprise-grade security intelligence.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from domain.monitoring.advanced_security_engine import (SecurityReport,
                                                        SecurityVulnerability,
                                                        ThreatLevel,
                                                        get_security_engine)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security", tags=["Advanced Security"])


class SecurityScanRequest(BaseModel):
    """Request for comprehensive security scan"""

    target: str = Field(..., description="Target to scan")
    scan_config: Dict[str, Any] = Field(..., description="Scan configuration")


class QuickSecurityCheckRequest(BaseModel):
    """Request for quick security check"""

    target: str = Field(..., description="Target to check")
    check_type: str = Field(default="basic", description="Type of check")


class CodeSecurityScanRequest(BaseModel):
    """Request for code security scanning"""

    code_content: str = Field(..., description="Source code to scan")
    file_path: Optional[str] = Field(None, description="File path for context")


@router.post("/scan/comprehensive")
async def comprehensive_security_scan(
    request: SecurityScanRequest, current_user: dict = Depends(get_current_user)
):
    """Perform comprehensive security assessment"""
    try:
        logger.info(f"🔒 Security scan requested for: {request.target}")

        # Get security engine
        engine = await get_security_engine()

        # Perform scan
        report = await engine.comprehensive_security_scan(
            request.target, request.scan_config
        )

        # Count vulnerabilities by severity
        vuln_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in report.vulnerabilities:
            severity = vuln.threat_level.value
            if severity in vuln_counts:
                vuln_counts[severity] += 1

        response_data = {
            "report_id": report.report_id,
            "target": report.target,
            "vulnerabilities_count": len(report.vulnerabilities),
            "severity_breakdown": vuln_counts,
            "risk_score": report.risk_score,
            "recommendations": report.recommendations,
            "scan_duration": report.scan_duration,
            "created_at": report.created_at.isoformat(),
        }

        logger.info(
            f"✅ Security scan completed: {len(report.vulnerabilities)} vulnerabilities"
        )
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"❌ Security scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/code")
async def scan_code_security(
    request: CodeSecurityScanRequest, current_user: dict = Depends(get_current_user)
):
    """Scan source code for security vulnerabilities"""
    try:
        logger.info("🔍 Code security scan requested")

        # Get security engine
        engine = await get_security_engine()

        # Perform code scan
        vulnerabilities = await engine.scan_code_security(
            request.code_content, request.file_path or "uploaded_code"
        )

        # Format response
        vulnerability_data = []
        for vuln in vulnerabilities:
            vulnerability_data.append(
                {
                    "vulnerability_id": vuln.vulnerability_id,
                    "type": vuln.vulnerability_type.value,
                    "threat_level": vuln.threat_level.value,
                    "title": vuln.title,
                    "description": vuln.description,
                    "location": vuln.location,
                    "remediation": vuln.remediation,
                    "confidence": vuln.confidence,
                }
            )

        return JSONResponse(
            content={
                "scan_type": "code_security",
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerability_data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Code scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/quick")
async def quick_security_check(
    request: QuickSecurityCheckRequest, current_user: dict = Depends(get_current_user)
):
    """Perform quick security check"""
    try:
        logger.info(f"⚡ Quick security check for: {request.target}")

        # Get security engine
        engine = await get_security_engine()

        # Perform quick check
        result = await engine.quick_security_check(request.target, request.check_type)

        logger.info(f"✅ Quick check completed: {result['issues_found']} issues")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"❌ Quick check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_security_metrics(current_user: dict = Depends(get_current_user)):
    """Get security engine metrics"""
    try:
        engine = await get_security_engine()
        metrics = engine.get_security_metrics()
        return JSONResponse(content=metrics)

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_security_status(current_user: dict = Depends(get_current_user)):
    """Get security engine status"""
    try:
        engine = await get_security_engine()
        metrics = engine.get_security_metrics()

        return JSONResponse(
            content={
                "engine_status": "active",
                "system_health": "healthy",
                "scans_performed": metrics["metrics"]["scans_performed"],
                "critical_issues_detected": metrics["metrics"]["critical_issues"],
                "last_updated": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "advanced_security",
        }
    )
