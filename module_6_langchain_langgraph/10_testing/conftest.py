"""
10_testing/conftest.py
Shared pytest fixtures for all AI agent tests.
"""

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage


@pytest.fixture(autouse=True)
def no_real_api_calls(monkeypatch):
    """
    Safety: prevent real API calls in every test automatically.
    Tests should NEVER call real LLM APIs — it costs money and is slow.
    """
    monkeypatch.setenv("OPENAI_API_KEY",    "sk-test-fake-key-do-not-use")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key-do-not-use")


@pytest.fixture
def mock_llm_direct_answer():
    """LLM that always gives a direct answer (no tool calls)."""
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="Direct answer.", tool_calls=[])
    mock.bind_tools.return_value = mock
    return mock


@pytest.fixture
def mock_llm_with_tool_call():
    """LLM that first calls a tool, then gives the final answer."""
    mock = MagicMock()
    mock.invoke.side_effect = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "calculator",
                "args": {"expression": "10 * 10"},
                "id":   "call_test_001",
                "type": "tool_call",
            }]
        ),
        AIMessage(content="10 * 10 = 100", tool_calls=[]),
    ]
    mock.bind_tools.return_value = mock
    return mock
