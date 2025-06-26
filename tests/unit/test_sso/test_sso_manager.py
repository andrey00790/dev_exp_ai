"""
Unit tests for SSO Manager

Tests SSO provider management, authentication flows, and session handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi import HTTPException

from app.security.sso.sso_manager import SSOManager
from app.security.sso.models import SSOProvider, SSOUser, SSOSession, SSOProviderType


class TestSSOManager:
    """Test suite for SSOManager"""
    
    @pytest.fixture
    def sso_manager(self):
        """Create SSOManager instance for testing"""
        return SSOManager(base_url="http://localhost:8000")
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_saml_provider(self):
        """Mock SAML provider"""
        return SSOProvider(
            id=1,
            name="Test SAML",
            provider_type=SSOProviderType.SAML,
            enabled=True,
            entity_id="test-entity",
            sso_url="https://test.com/sso",
            slo_url="https://test.com/slo",
            x509_cert="test-cert"
        )
    
    @pytest.fixture
    def mock_oauth_provider(self):
        """Mock OAuth provider"""
        return SSOProvider(
            id=2,
            name="Test OAuth",
            provider_type=SSOProviderType.OAUTH_GOOGLE,
            enabled=True,
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    def test_initialization(self, sso_manager):
        """Test SSOManager initialization"""
        assert sso_manager.base_url == "http://localhost:8000"
        assert sso_manager.saml_handler is not None
        assert sso_manager.oauth_handler is not None
    
    def test_get_available_providers(self, sso_manager, mock_db, mock_saml_provider, mock_oauth_provider):
        """Test getting available SSO providers"""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_saml_provider, mock_oauth_provider]
        mock_db.query.return_value = mock_query
        
        # Test
        providers = sso_manager.get_available_providers(mock_db)
        
        # Assertions
        assert len(providers) == 2
        assert providers[0]["name"] == "Test SAML"
        assert providers[1]["name"] == "Test OAuth"
        assert "login_url" in providers[0]
        assert "available" in providers[0]
    
    def test_get_login_url_saml(self, sso_manager, mock_saml_provider):
        """Test getting login URL for SAML provider"""
        url = sso_manager._get_login_url(mock_saml_provider)
        assert url == "http://localhost:8000/api/v1/auth/sso/saml/1/login"
    
    def test_get_login_url_oauth(self, sso_manager, mock_oauth_provider):
        """Test getting login URL for OAuth provider"""
        url = sso_manager._get_login_url(mock_oauth_provider)
        assert url == "http://localhost:8000/api/v1/auth/sso/oauth/2/login"
    
    @pytest.mark.asyncio
    async def test_initiate_saml_login(self, sso_manager, mock_db, mock_saml_provider):
        """Test initiating SAML login"""
        mock_request = Mock()
        
        # Mock SAML handler
        with patch.object(sso_manager.saml_handler, 'initiate_login', new_callable=AsyncMock) as mock_initiate:
            mock_initiate.return_value = "https://saml-redirect-url"
            
            # Mock _get_provider
            with patch.object(sso_manager, '_get_provider', return_value=mock_saml_provider):
                result = await sso_manager.initiate_login(1, mock_request, mock_db)
                
                assert result["type"] == "redirect"
                assert result["url"] == "https://saml-redirect-url"
                assert result["provider"] == "Test SAML"
    
    @pytest.mark.asyncio
    async def test_initiate_oauth_login(self, sso_manager, mock_db, mock_oauth_provider):
        """Test initiating OAuth login"""
        mock_request = Mock()
        
        # Mock OAuth handler
        with patch.object(sso_manager.oauth_handler, 'initiate_login', new_callable=AsyncMock) as mock_initiate:
            mock_initiate.return_value = ("https://oauth-url", "test-state")
            
            # Mock _get_provider
            with patch.object(sso_manager, '_get_provider', return_value=mock_oauth_provider):
                result = await sso_manager.initiate_login(2, mock_request, mock_db)
                
                assert result["type"] == "redirect"
                assert result["url"] == "https://oauth-url"
                assert result["state"] == "test-state"
                assert result["provider"] == "Test OAuth"
    
    @pytest.mark.asyncio
    async def test_initiate_login_disabled_provider(self, sso_manager, mock_db, mock_saml_provider):
        """Test error when trying to use disabled provider"""
        mock_saml_provider.enabled = False
        mock_request = Mock()
        
        with patch.object(sso_manager, '_get_provider', return_value=mock_saml_provider):
            with pytest.raises(HTTPException) as exc_info:
                await sso_manager.initiate_login(1, mock_request, mock_db)
            
            assert exc_info.value.status_code == 400
            assert "disabled" in str(exc_info.value.detail)
    
    def test_create_provider_saml(self, sso_manager, mock_db):
        """Test creating SAML provider"""
        provider_data = {
            "name": "New SAML Provider",
            "provider_type": SSOProviderType.SAML,
            "entity_id": "new-entity",
            "sso_url": "https://new.com/sso",
            "enabled": True
        }
        
        # Mock validation
        with patch.object(sso_manager, '_validate_provider_config'):
            result = sso_manager.create_provider(mock_db, provider_data, created_by=1)
            
            # Verify provider was added to database
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            
            assert result.name == "New SAML Provider"
            assert result.provider_type == SSOProviderType.SAML
    
    def test_create_provider_oauth(self, sso_manager, mock_db):
        """Test creating OAuth provider"""
        provider_data = {
            "name": "New OAuth Provider",
            "provider_type": SSOProviderType.OAUTH_GOOGLE,
            "client_id": "new-client-id",
            "client_secret": "new-client-secret",
            "enabled": True
        }
        
        # Mock validation
        with patch.object(sso_manager, '_validate_provider_config'):
            result = sso_manager.create_provider(mock_db, provider_data, created_by=1)
            
            # Verify provider was added to database
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            
            assert result.name == "New OAuth Provider"
            assert result.provider_type == SSOProviderType.OAUTH_GOOGLE
    
    def test_validate_provider_config_saml_valid(self, sso_manager):
        """Test SAML provider validation with valid config"""
        provider_data = {
            "name": "Test SAML",
            "provider_type": SSOProviderType.SAML,
            "entity_id": "test-entity",
            "sso_url": "https://test.com/sso"
        }
        
        # Should not raise exception
        sso_manager._validate_provider_config(provider_data)
    
    def test_validate_provider_config_saml_missing_fields(self, sso_manager):
        """Test SAML provider validation with missing fields"""
        provider_data = {
            "name": "Test SAML",
            "provider_type": SSOProviderType.SAML
            # Missing entity_id and sso_url
        }
        
        with pytest.raises(HTTPException) as exc_info:
            sso_manager._validate_provider_config(provider_data)
        
        assert exc_info.value.status_code == 400
        assert "Missing required fields" in str(exc_info.value.detail)
    
    def test_validate_provider_config_oauth_valid(self, sso_manager):
        """Test OAuth provider validation with valid config"""
        provider_data = {
            "name": "Test OAuth",
            "provider_type": SSOProviderType.OAUTH_GOOGLE,
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
        
        # Should not raise exception
        sso_manager._validate_provider_config(provider_data)
    
    def test_validate_provider_config_invalid_type(self, sso_manager):
        """Test provider validation with invalid type"""
        provider_data = {
            "name": "Test Provider",
            "provider_type": "invalid_type"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            sso_manager._validate_provider_config(provider_data)
        
        assert exc_info.value.status_code == 400
        assert "Invalid provider type" in str(exc_info.value.detail)
    
    def test_get_provider_found(self, sso_manager, mock_db, mock_saml_provider):
        """Test getting existing provider"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_saml_provider
        mock_db.query.return_value = mock_query
        
        result = sso_manager._get_provider(mock_db, 1)
        
        assert result == mock_saml_provider
    
    def test_get_provider_not_found(self, sso_manager, mock_db):
        """Test getting non-existent provider"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            sso_manager._get_provider(mock_db, 999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
    
    def test_update_provider(self, sso_manager, mock_db, mock_saml_provider):
        """Test updating provider configuration"""
        update_data = {
            "name": "Updated SAML Provider",
            "enabled": False,
            "sso_url": "https://updated.com/sso"
        }
        
        with patch.object(sso_manager, '_get_provider', return_value=mock_saml_provider):
            result = sso_manager.update_provider(mock_db, 1, update_data)
            
            # Verify updates were applied
            assert result.name == "Updated SAML Provider"
            assert result.enabled == False
            assert result.sso_url == "https://updated.com/sso"
            
            mock_db.commit.assert_called_once()
    
    def test_delete_provider_with_active_users(self, sso_manager, mock_db, mock_saml_provider):
        """Test deleting provider with active users (should fail)"""
        # Mock query that returns active users
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        mock_db.query.return_value = mock_query
        
        with patch.object(sso_manager, '_get_provider', return_value=mock_saml_provider):
            with pytest.raises(HTTPException) as exc_info:
                sso_manager.delete_provider(mock_db, 1)
            
            assert exc_info.value.status_code == 400
            assert "5 active users" in str(exc_info.value.detail)
    
    def test_delete_provider_success(self, sso_manager, mock_db, mock_saml_provider):
        """Test successful provider deletion"""
        # Mock query that returns no active users
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 0
        mock_db.query.return_value = mock_query
        
        with patch.object(sso_manager, '_get_provider', return_value=mock_saml_provider):
            sso_manager.delete_provider(mock_db, 1)
            
            mock_db.delete.assert_called_once_with(mock_saml_provider)
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_logout(self, sso_manager, mock_db):
        """Test SSO logout handling"""
        # Mock active sessions
        mock_session1 = Mock()
        mock_session1.active = True
        mock_session2 = Mock()
        mock_session2.active = True
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_session1, mock_session2]
        mock_db.query.return_value = mock_query
        
        result = await sso_manager.handle_logout(user_id=1, provider_id=None, db=mock_db)
        
        # Verify sessions were deactivated
        assert mock_session1.active == False
        assert mock_session1.logout_reason == "manual"
        assert mock_session2.active == False
        assert mock_session2.logout_reason == "manual"
        
        mock_db.commit.assert_called_once()
    
    def test_get_user_sso_info(self, sso_manager, mock_db):
        """Test getting user SSO information"""
        mock_sso_user = Mock()
        mock_sso_user.to_dict.return_value = {
            "id": 1,
            "external_user_id": "test@example.com",
            "provider_name": "Test Provider"
        }
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_sso_user]
        mock_db.query.return_value = mock_query
        
        result = sso_manager.get_user_sso_info(mock_db, user_id=1)
        
        assert len(result) == 1
        assert result[0]["external_user_id"] == "test@example.com"
    
    def test_check_provider_availability_saml(self, sso_manager, mock_saml_provider):
        """Test checking SAML provider availability"""
        with patch.object(sso_manager.saml_handler, 'is_available', return_value=True):
            result = sso_manager._check_provider_availability(mock_saml_provider)
            assert result == True
    
    def test_check_provider_availability_oauth(self, sso_manager, mock_oauth_provider):
        """Test checking OAuth provider availability"""
        with patch.object(sso_manager.oauth_handler, 'is_available', return_value=True):
            result = sso_manager._check_provider_availability(mock_oauth_provider)
            assert result == True


class TestSSOConfig:
    """Test suite for SSOConfig"""
    
    def test_default_config(self):
        """Test default SSO configuration"""
        from app.security.sso.sso_manager import SSOConfig
        
        config = SSOConfig()
        assert config.session_timeout == 3600
        assert config.max_sessions_per_user == 5
        assert config.require_encryption == True
        assert config.allowed_clock_skew == 300
    
    def test_config_from_env(self):
        """Test loading configuration from environment"""
        from app.security.sso.sso_manager import SSOConfig
        
        with patch.dict('os.environ', {
            'SSO_SESSION_TIMEOUT': '7200',
            'SSO_MAX_SESSIONS': '10',
            'SSO_REQUIRE_ENCRYPTION': 'false',
            'SSO_CLOCK_SKEW': '600'
        }):
            config = SSOConfig.from_env()
            assert config.session_timeout == 7200
            assert config.max_sessions_per_user == 10
            assert config.require_encryption == False
            assert config.allowed_clock_skew == 600 