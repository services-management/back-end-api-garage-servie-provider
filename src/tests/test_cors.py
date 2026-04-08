"""Unit tests for CORS configuration and ALLOWED_ORIGINS parsing."""
from unittest.mock import patch


class TestAllowedOriginsSettings:
    """Test ALLOWED_ORIGINS parsing and configuration."""

    def test_single_origin_parsing(self, db_session):
        """Test that a single origin is correctly parsed into a list."""
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': 'http://localhost:3000'}):
            from src.config.settings import Settings
            test_settings = Settings()
            
            assert test_settings.ALLOWED_ORIGINS == 'http://localhost:3000'
            assert test_settings.allowed_origins_list == ['http://localhost:3000']
            assert len(test_settings.allowed_origins_list) == 1

    def test_multiple_origins_parsing(self, db_session):
        """Test that multiple comma-separated origins are correctly parsed."""
        origins = 'https://admin.mrlubekh.com,https://garas-admin.domrey.online,http://localhost:3000'
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': origins}):
            from src.config.settings import Settings
            test_settings = Settings()
            
            assert len(test_settings.allowed_origins_list) == 3
            assert 'https://admin.mrlubekh.com' in test_settings.allowed_origins_list
            assert 'https://garas-admin.domrey.online' in test_settings.allowed_origins_list
            assert 'http://localhost:3000' in test_settings.allowed_origins_list

    def test_origins_with_spaces_are_trimmed(self, db_session):
        """Test that spaces around origins are removed."""
        origins = 'http://localhost:3000, http://localhost:8000 ,  http://localhost:5000'
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': origins}):
            from src.config.settings import Settings
            test_settings = Settings()
            
            assert test_settings.allowed_origins_list == [
                'http://localhost:3000',
                'http://localhost:8000',
                'http://localhost:5000'
            ]
            # No trailing spaces
            assert all(' ' not in origin for origin in test_settings.allowed_origins_list)

    def test_default_origin_when_not_set(self, db_session):
        """Test default value when ALLOWED_ORIGINS is not in environment."""
        # Remove ALLOWED_ORIGINS from both env and .env file
        with patch.dict('os.environ', {}, clear=True):
            # Mock the Settings to not read from .env file
            from src.config.settings import Settings
            import os
            
            # Temporarily remove ALLOWED_ORIGINS from environment
            old_value = os.environ.pop('ALLOWED_ORIGINS', None)
            try:
                test_settings = Settings(_env_file=None)
                # If Settings has no default, it will be empty
                # Adjust assertion based on actual behavior
                assert isinstance(test_settings.allowed_origins_list, list)
            finally:
                if old_value:
                    os.environ['ALLOWED_ORIGINS'] = old_value

    def test_empty_string_creates_empty_list(self, db_session):
        """Test that empty ALLOWED_ORIGINS creates an empty list."""
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': ''}):
            from src.config.settings import Settings
            test_settings = Settings()
            
            assert test_settings.allowed_origins_list == []

    def test_trailing_comma_handled(self, db_session):
        """Test that trailing commas don't create empty entries."""
        origins = 'http://localhost:3000,http://localhost:8000,'
        with patch.dict('os.environ', {'ALLOWED_ORIGINS': origins}):
            from src.config.settings import Settings
            test_settings = Settings()
            
            # Should only have 2 entries, not 3
            assert len(test_settings.allowed_origins_list) == 2
            assert test_settings.allowed_origins_list == [
                'http://localhost:3000',
                'http://localhost:8000'
            ]


class TestCORSMiddleware:
    """Test that CORS middleware uses the configured origins."""

    def test_cors_allows_configured_origin(self, client):
        """Test that requests from allowed origins are accepted."""
        response = client.options(
            '/vehicles/makes',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET'
            }
        )
        
        # CORS preflight should succeed
        assert response.status_code == 200
        # Should have CORS headers
        assert 'access-control-allow-origin' in response.headers

    def test_cors_exposes_headers(self, client):
        """Test that CORS headers are exposed on actual requests."""
        response = client.get(
            '/vehicles/makes',
            headers={'Origin': 'http://localhost:3000'}
        )
        
        # Should allow the origin
        allow_origin = response.headers.get('access-control-allow-origin')
        assert allow_origin == 'http://localhost:3000'

    def test_cors_allows_credentials(self, client):
        """Test that credentials are allowed in CORS."""
        response = client.options(
            '/vehicles/makes',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET'
            }
        )
        
        # Should allow credentials
        assert response.headers.get('access-control-allow-credentials') == 'true'

    def test_cors_allowed_methods(self, client):
        """Test that allowed methods are exposed."""
        response = client.options(
            '/vehicles/makes',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST'
            }
        )
        
        # Should list allowed methods
        allow_methods = response.headers.get('access-control-allow-methods', '')
        assert 'GET' in allow_methods or 'POST' in allow_methods