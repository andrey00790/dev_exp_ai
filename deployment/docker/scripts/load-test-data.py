#!/usr/bin/env python3
"""
Test Data Loader
Загружает тестовые данные во все системы для E2E тестирования
"""

import os
import sys
import time
import json
import requests
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDataLoader:
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL', 'http://test-jira:8080')
        self.confluence_url = os.getenv('CONFLUENCE_URL', 'http://test-confluence:8090')
        self.gitlab_url = os.getenv('GITLAB_URL', 'http://test-gitlab')
        self.app_url = os.getenv('APP_URL', 'http://test-app:8000')
        self.test_data_path = Path('/app/test-data')
        
    def wait_for_service(self, url: str, service_name: str, timeout: int = 300):
        """Ожидание доступности сервиса"""
        logger.info(f"Waiting for {service_name} at {url}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/status", timeout=10)
                if response.status_code == 200:
                    logger.info(f"{service_name} is ready!")
                    return True
            except requests.exceptions.RequestException:
                logger.debug(f"{service_name} not ready yet, retrying...")
                time.sleep(5)
                
        logger.error(f"{service_name} failed to start within {timeout} seconds")
        return False
    
    def load_jira_data(self):
        """Загрузка данных в Jira"""
        logger.info("Loading JIRA test data...")
        
        # Проверяем доступность Jira
        if not self.wait_for_service(self.jira_url, "JIRA"):
            return False
            
        # Загружаем тестовые данные
        jira_data_path = self.test_data_path / 'jira'
        if jira_data_path.exists():
            logger.info(f"Loading JIRA data from {jira_data_path}")
            # Здесь будет логика загрузки данных в Jira
            return True
        else:
            logger.warning(f"JIRA test data not found at {jira_data_path}")
            return False
    
    def load_confluence_data(self):
        """Загрузка данных в Confluence"""
        logger.info("Loading Confluence test data...")
        
        if not self.wait_for_service(self.confluence_url, "Confluence"):
            return False
            
        confluence_data_path = self.test_data_path / 'confluence'
        if confluence_data_path.exists():
            logger.info(f"Loading Confluence data from {confluence_data_path}")
            # Здесь будет логика загрузки данных в Confluence
            return True
        else:
            logger.warning(f"Confluence test data not found at {confluence_data_path}")
            return False
    
    def load_gitlab_data(self):
        """Загрузка данных в GitLab"""
        logger.info("Loading GitLab test data...")
        
        if not self.wait_for_service(self.gitlab_url, "GitLab"):
            return False
            
        gitlab_data_path = self.test_data_path / 'gitlab'
        if gitlab_data_path.exists():
            logger.info(f"Loading GitLab data from {gitlab_data_path}")
            # Здесь будет логика загрузки данных в GitLab
            return True
        else:
            logger.warning(f"GitLab test data not found at {gitlab_data_path}")
            return False
    
    def load_app_data(self):
        """Загрузка данных в приложение"""
        logger.info("Loading application test data...")
        
        if not self.wait_for_service(self.app_url, "AI Assistant"):
            return False
            
        try:
            # Создание тестовых пользователей
            test_users = [
                {"email": "test@example.com", "password": "testpass123", "role": "user"},
                {"email": "admin@example.com", "password": "adminpass123", "role": "admin"}
            ]
            
            for user in test_users:
                try:
                    response = requests.post(
                        f"{self.app_url}/auth/register",
                        json=user,
                        timeout=10
                    )
                    if response.status_code in [200, 201, 409]:  # 409 = already exists
                        logger.info(f"User {user['email']} created/exists")
                    else:
                        logger.warning(f"Failed to create user {user['email']}: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error creating user {user['email']}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading app data: {e}")
            return False
    
    def run(self):
        """Запуск загрузки всех тестовых данных"""
        logger.info("Starting test data loading process...")
        
        success = True
        
        # Загружаем данные в каждую систему
        try:
            # Основное приложение
            if not self.load_app_data():
                success = False
                
            # Внешние системы (только если они запущены с профилем e2e)
            if os.getenv('LOAD_E2E_DATA', 'false').lower() == 'true':
                if not self.load_jira_data():
                    success = False
                    
                if not self.load_confluence_data():
                    success = False
                    
                if not self.load_gitlab_data():
                    success = False
                    
        except Exception as e:
            logger.error(f"Error during data loading: {e}")
            success = False
        
        if success:
            logger.info("✅ Test data loading completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Test data loading failed!")
            sys.exit(1)

if __name__ == "__main__":
    loader = TestDataLoader()
    loader.run() 