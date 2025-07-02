"""
Data Sources API - Compatibility module
"""

from fastapi import APIRouter
import asyncio


# Create router for compatibility
router = APIRouter()


async def initialize_sync_scheduler():
    """Initialize sync scheduler - stub implementation"""
    return {"status": "initialized", "message": "Sync scheduler initialized successfully"}


async def shutdown_sync_scheduler():
    """Shutdown sync scheduler - stub implementation"""
    return {"status": "shutdown", "message": "Sync scheduler shutdown successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data_sources"}


@router.get("/sources")
async def list_data_sources():
    """List data sources - stub implementation"""
    return {
        "sources": [
            {"id": "confluence", "type": "confluence", "status": "active"},
            {"id": "jira", "type": "jira", "status": "active"},
            {"id": "gitlab", "type": "gitlab", "status": "active"}
        ]
    }


@router.post("/sync")
async def sync_data_sources():
    """Sync data sources - stub implementation"""
    return {"status": "success", "message": "Sync completed successfully"} 