"""
Tests for the settings module.
"""

import os
import pytest
from pathlib import Path

# Import from test_framework to ensure consistent test setup
from tests.test_framework import BaseTestCase


class TestSettings(BaseTestCase):
    """Test cases for the settings module."""
    
    def test_settings_load(self):
        """Test that settings load correctly."""
        try:
            from src.utils.settings import settings
            
            # Check that essential settings are loaded
            self.assertIsNotNone(settings.env)
            self.assertIsNotNone(settings.database_uri)
            self.assertIsNotNone(settings.session_storage_uri)
            self.assertIsNotNone(settings.content_path)
            
            # Check that feature flags are loaded
            self.assertIsNotNone(settings.feature_flags)
            self.assertIn("use_new_kb", settings.feature_flags.model_dump())
            self.assertIn("use_new_api", settings.feature_flags.model_dump())
            
            # Check that paths are correctly set
            self.assertTrue(Path(settings.content_path).exists())
            
            # The test should reach this point without errors
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import settings: {e}")
        except Exception as e:
            self.fail(f"Error in settings: {e}")
    
    def test_feature_flags(self):
        """Test that feature flags can be accessed."""
        try:
            from src.utils.settings import settings
            
            # Check feature flags access
            flags = settings.feature_flags
            
            # Test accessing individual flags
            self.assertIsInstance(flags.use_new_kb, bool)
            self.assertIsInstance(flags.use_new_api, bool)
            self.assertIsInstance(flags.use_postgres, bool)
            self.assertIsInstance(flags.use_redis, bool)
            
            # Check that the flags reflect environment variables
            self.assertEqual(flags.use_new_kb, os.environ.get("USE_NEW_KB", "false").lower() == "true")
            self.assertEqual(flags.use_new_api, os.environ.get("USE_NEW_API", "false").lower() == "true")
            
        except ImportError as e:
            self.fail(f"Failed to import settings: {e}")
        except Exception as e:
            self.fail(f"Error in feature flags: {e}")


# For pytest style tests
def test_settings_module_load():
    """Pytest style test for settings module loading."""
    # Import settings
    from src.utils.settings import settings
    
    # Verify basic settings
    assert settings is not None
    assert settings.env == "test"
    assert settings.log_level in ["INFO", "ERROR", "DEBUG"]  # Allow any valid log level
    
    # Check feature flags
    assert hasattr(settings, "feature_flags")
    flags = settings.feature_flags
    assert hasattr(flags, "use_new_kb")
    assert hasattr(flags, "use_postgres")
    assert hasattr(flags, "use_new_api")
    
    # Check security settings
    assert hasattr(settings, "jwt_secret")
    assert settings.jwt_algorithm == "HS256"
    
    # For this test to pass, all assertions must be true
    assert True 