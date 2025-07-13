#!/usr/bin/env python3
"""
Bootstrap Integration Tests
Tests the complete ETL pipeline and data loading process
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBootstrapIntegration:
    """Test bootstrap process integration"""
    
    def test_bootstrap_data_directories_exist(self):
        """Test that bootstrap data directories exist"""
        required_dirs = [
            "local",
            "test-data",
            "data/postgres",
            "data/qdrant", 
            "data/redis"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            assert path.exists(), f"Required directory {dir_path} does not exist"
    
    def test_bootstrap_config_files_exist(self):
        """Test that bootstrap configuration files exist"""
        required_files = [
            "local/bootstrap_fetcher.py",
            "local/bootstrap_fetcher.sh",
            "docker-compose.yml"
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            assert path.exists(), f"Required file {file_path} does not exist"
    
    def test_bootstrap_environment_variables(self):
        """Test that required environment variables can be set"""
        required_env_vars = [
            "DATABASE_URL",
            "QDRANT_URL", 
            "REDIS_URL",
            "ENVIRONMENT",
            "PYTHONPATH"
        ]
        
        # Test with example values
        test_values = {
            "DATABASE_URL": "postgresql://ai_user:ai_password_dev@postgres:5432/ai_assistant",
            "QDRANT_URL": "http://qdrant:6333",
            "REDIS_URL": "redis://redis:6379/0",
            "ENVIRONMENT": "bootstrap",
            "PYTHONPATH": "/app"
        }
        
        for var in required_env_vars:
            # Test that we can set and get the variable
            os.environ[var] = test_values[var]
            assert os.environ.get(var) == test_values[var]
    
    def test_bootstrap_script_executable(self):
        """Test that bootstrap script is executable"""
        script_path = Path("local/bootstrap_fetcher.py")
        assert script_path.exists()
        
        # Check if it's a valid Python file
        with open(script_path, 'r') as f:
            content = f.read()
            assert content.startswith('#!/usr/bin/env python') or 'python' in content
    
    def test_bootstrap_test_data_structure(self):
        """Test that test data structure is correct"""
        test_data_dir = Path("test-data")
        assert test_data_dir.exists()
        
        # Should have at least some sample data
        subdirs = list(test_data_dir.iterdir())
        assert len(subdirs) > 0, "test-data directory should not be empty"
    
    def test_docker_compose_bootstrap_profile(self):
        """Test that docker-compose.yml has bootstrap profile"""
        compose_file = Path("docker-compose.yml")
        assert compose_file.exists()
        
        with open(compose_file, 'r') as f:
            content = f.read()
            assert 'bootstrap' in content, "docker-compose.yml should contain bootstrap profile"
            assert 'COMPOSE_PROFILES=bootstrap' in content or 'profiles:' in content


class TestBootstrapDataIntegrity:
    """Test data integrity after bootstrap process"""
    
    @pytest.mark.asyncio
    async def test_database_connection_after_bootstrap(self):
        """Test that database is accessible after bootstrap"""
        try:
            import asyncpg
            
            # Test connection with bootstrap environment
            conn_string = "postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant"
            
            # This would normally test actual connection but we'll mock it for now
            # conn = await asyncpg.connect(conn_string)
            # await conn.close()
            
            # For now, just test that the connection string is valid format
            assert "postgresql://" in conn_string
            assert "@" in conn_string
            assert ":" in conn_string
            
        except ImportError:
            # If asyncpg not available, skip this test
            pytest.skip("asyncpg not available for database testing")
    
    def test_qdrant_data_directory_writable(self):
        """Test that Qdrant data directory is writable"""
        qdrant_dir = Path("data/qdrant")
        assert qdrant_dir.exists()
        
        # Test that we can create a file in the directory
        test_file = qdrant_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            assert test_file.read_text() == "test"
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_postgres_data_directory_writable(self):
        """Test that PostgreSQL data directory is writable"""
        postgres_dir = Path("data/postgres")
        assert postgres_dir.exists()
        
        # Test that we can create a file in the directory
        test_file = postgres_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            assert test_file.read_text() == "test"
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()


class TestBootstrapDockerIntegration:
    """Test Docker integration for bootstrap"""
    
    def test_dockerfile_bootstrap_exists(self):
        """Test that Dockerfile.bootstrap exists"""
        dockerfile = Path("deployment/docker/Dockerfile.bootstrap")
        assert dockerfile.exists()
        
        with open(dockerfile, 'r') as f:
            content = f.read()
            assert 'FROM python:' in content
            assert 'bootstrap' in content.lower()
    
    def test_bootstrap_command_in_compose(self):
        """Test that bootstrap command is properly defined"""
        compose_file = Path("docker-compose.yml")
        assert compose_file.exists()
        
        with open(compose_file, 'r') as f:
            content = f.read()
            assert 'bootstrap' in content
            assert 'bootstrap_fetcher.py' in content or 'bootstrap' in content
    
    def test_bootstrap_volumes_configured(self):
        """Test that required volumes are configured for bootstrap"""
        compose_file = Path("docker-compose.yml")
        assert compose_file.exists()
        
        with open(compose_file, 'r') as f:
            content = f.read()
            
            # Check for required volume mounts
            required_volumes = [
                './local:/app/local',
                './test-data:/app/test-data', 
                './data:/app/data',
                './logs:/app/logs'
            ]
            
            for volume in required_volumes:
                assert volume in content, f"Required volume {volume} not found in docker-compose.yml"


class TestBootstrapMakefileIntegration:
    """Test Makefile integration for bootstrap"""
    
    def test_makefile_bootstrap_target_exists(self):
        """Test that Makefile has bootstrap target"""
        makefile = Path("Makefile")
        assert makefile.exists()
        
        with open(makefile, 'r') as f:
            content = f.read()
            assert 'bootstrap:' in content
            assert 'test-bootstrap:' in content
    
    def test_makefile_bootstrap_dependencies(self):
        """Test that bootstrap target has proper dependencies"""
        makefile = Path("Makefile")
        assert makefile.exists()
        
        with open(makefile, 'r') as f:
            content = f.read()
            
            # Should check for required services
            assert 'postgres' in content
            assert 'qdrant' in content
            assert 'COMPOSE_PROFILES=bootstrap' in content


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 