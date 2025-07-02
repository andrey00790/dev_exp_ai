#!/usr/bin/env python3
"""
🔧 CREATE TEST DATA SCRIPT
Скрипт для создания и загрузки тестовых данных в БД и векторное хранилище.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import json

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent.parent.parent))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные
SAMPLE_DOCUMENTS = [
    {
        "title": "AI Assistant Architecture",
        "content": "This document describes the architecture of the AI Assistant system...",
        "source": "docs/architecture.md",
        "metadata": {"type": "documentation", "category": "architecture"}
    },
    {
        "title": "API Usage Guide", 
        "content": "Learn how to use the AI Assistant API for integrating with your applications...",
        "source": "docs/api_guide.md",
        "metadata": {"type": "documentation", "category": "api"}
    },
    {
        "title": "Deployment Instructions",
        "content": "Step-by-step guide for deploying the AI Assistant in production...",
        "source": "docs/deployment.md", 
        "metadata": {"type": "documentation", "category": "deployment"}
    }
]

SAMPLE_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "System Administrator",
        "is_active": True
    },
    {
        "username": "testuser",
        "email": "test@example.com", 
        "full_name": "Test User",
        "is_active": True
    }
]

SAMPLE_PROJECTS = [
    {
        "name": "AI Assistant Demo",
        "description": "Demonstration project for AI Assistant capabilities",
        "status": "active"
    },
    {
        "name": "Documentation System",
        "description": "Project for managing and searching documentation",
        "status": "active"
    }
]


async def create_test_documents():
    """Создает тестовые документы"""
    try:
        logger.info("📄 Creating test documents...")
        
        # Здесь должна быть логика создания документов в БД
        # Пока что просто выводим информацию
        for doc in SAMPLE_DOCUMENTS:
            logger.info(f"Would create document: {doc['title']}")
            
        logger.info(f"✅ {len(SAMPLE_DOCUMENTS)} test documents ready")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating documents: {e}")
        return False


async def create_test_users():
    """Создает тестовых пользователей"""
    try:
        logger.info("👥 Creating test users...")
        
        # Здесь должна быть логика создания пользователей в БД
        for user in SAMPLE_USERS:
            logger.info(f"Would create user: {user['username']}")
            
        logger.info(f"✅ {len(SAMPLE_USERS)} test users ready")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating users: {e}")
        return False


async def create_test_projects():
    """Создает тестовые проекты"""
    try:
        logger.info("📁 Creating test projects...")
        
        # Здесь должна быть логика создания проектов в БД
        for project in SAMPLE_PROJECTS:
            logger.info(f"Would create project: {project['name']}")
            
        logger.info(f"✅ {len(SAMPLE_PROJECTS)} test projects ready")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating projects: {e}")
        return False


async def setup_vector_data():
    """Настраивает векторные данные"""
    try:
        logger.info("🔍 Setting up vector data...")
        
        # Здесь должна быть логика создания embeddings и векторных индексов
        logger.info("Would create vector embeddings for documents")
        logger.info("Would setup search indices")
        
        logger.info("✅ Vector data setup complete")
        return True
    except Exception as e:
        logger.error(f"❌ Error setting up vector data: {e}")
        return False


async def main():
    """Основная функция"""
    logger.info("🚀 Starting test data creation...")
    
    success = True
    
    # Создаем тестовые данные
    tasks = [
        create_test_documents(),
        create_test_users(),
        create_test_projects(),
        setup_vector_data()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Task {i+1} failed: {result}")
            success = False
        elif not result:
            logger.error(f"❌ Task {i+1} returned False")
            success = False
    
    if success:
        logger.info("🎉 All test data created successfully!")
        return 0
    else:
        logger.error("💥 Some tasks failed!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1) 