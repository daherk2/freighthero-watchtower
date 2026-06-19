"""Tests for LLM module with import guard."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestLLMImportGuard:
    """Tests for the LLM import guard."""

    def test_module_imports_without_langchain_openai(self):
        """Test that the module can be imported even without langchain_openai."""
        # The module should be importable - ChatOpenAI may be None
        import src.agent.llm as llm_module
        # get_llm should exist as a function
        assert callable(llm_module.get_llm)

    def test_get_llm_raises_import_error_when_not_installed(self):
        """Test that get_llm raises ImportError when ChatOpenAI is None."""
        import src.agent.llm as llm_module
        original = llm_module.ChatOpenAI
        try:
            llm_module.ChatOpenAI = None
            with pytest.raises(ImportError, match="langchain-openai"):
                llm_module.get_llm()
        finally:
            llm_module.ChatOpenAI = original

    def test_get_llm_returns_instance_when_available(self):
        """Test that get_llm returns a ChatOpenAI instance when available."""
        import src.agent.llm as llm_module
        mock_llm = MagicMock()
        original = llm_module.ChatOpenAI
        try:
            llm_module.ChatOpenAI = mock_llm
            result = llm_module.get_llm()
            assert result is not None
        finally:
            llm_module.ChatOpenAI = original