"""Tests for the main entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestMainModule:
    """Tests for the main module."""

    def test_main_module_imports(self):
        """Test that the main module can be imported."""
        import src.main
        assert hasattr(src.main, 'main')

    def test_main_function_exists(self):
        """Test that the main function exists."""
        from src.main import main
        assert callable(main)

    @patch("src.main.uvicorn")
    @patch("src.main.get_settings")
    def test_main_calls_uvicorn(self, mock_settings, mock_uvicorn):
        """Test that main calls uvicorn.run."""
        from src.main import main

        mock_settings_obj = MagicMock()
        mock_settings_obj.api_host = "0.0.0.0"
        mock_settings_obj.api_port = 8000
        mock_settings_obj.debug = False
        mock_settings.return_value = mock_settings_obj

        main()

        mock_uvicorn.run.assert_called_once()
        call_args = mock_uvicorn.run.call_args
        assert call_args[0][0] == "src.interfaces.app:app"
        assert call_args[1]["host"] == "0.0.0.0"
        assert call_args[1]["port"] == 8000