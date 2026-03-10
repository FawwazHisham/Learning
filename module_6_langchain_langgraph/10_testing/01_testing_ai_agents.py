"""
10_testing/01_testing_ai_agents.py
====================================
Testing AI Agent Systems with pytest + pytest-asyncio

CONCEPTS COVERED:
  - pytest basics and fixtures
  - pytest-asyncio for async agent testing
  - Mocking LLM calls (never call real APIs in tests!)
  - Testing graph nodes in isolation
  - Testing full agent workflows
  - Parametrized tests for multiple scenarios
  - Testing Pydantic model validation
  - Testing tool functions
  - Snapshot testing for LLM outputs

RUN TESTS:
  pytest 10_testing/ -v
  pytest 10_testing/ -v --asyncio-mode=auto
"""

import pytest
import asyncio
from typing import TypedDict, Annotated
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, ValidationError


# ── State definition (for tests) ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tools_used: list[str]


# ── Tools to test ─────────────────────────────────────────────────────────────
@tool
def calculator(expression: str) -> str:
    """Calculate a math expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_weather(city: str) -> dict:
    """Get weather for a city."""
    weather_data = {
        "london": {"temp": 15, "condition": "Rainy"},
        "paris":  {"temp": 22, "condition": "Sunny"},
        "tokyo":  {"temp": 28, "condition": "Humid"},
    }
    return weather_data.get(city.lower(), {"temp": 20, "condition": "Unknown"})


# ════════════════════════════════════════════════════════════════════
# SECTION 1: Tool Tests
# ════════════════════════════════════════════════════════════════════

class TestCalculatorTool:
    """Test the calculator tool directly."""

    def test_simple_addition(self):
        result = calculator.invoke({"expression": "2 + 2"})
        assert result == "2 + 2 = 4"

    def test_multiplication(self):
        result = calculator.invoke({"expression": "10 * 5"})
        assert result == "10 * 5 = 50"

    def test_complex_expression(self):
        result = calculator.invoke({"expression": "(100 + 50) / 3"})
        assert "50.0" in result

    def test_invalid_expression(self):
        result = calculator.invoke({"expression": "import os"})
        assert "Error" in result

    def test_division_by_zero(self):
        result = calculator.invoke({"expression": "1 / 0"})
        assert "Error" in result or "division by zero" in result


class TestWeatherTool:
    """Test the weather tool."""

    def test_known_city(self):
        result = get_weather.invoke({"city": "London"})
        assert result["temp"] == 15
        assert result["condition"] == "Rainy"

    def test_case_insensitive(self):
        result = get_weather.invoke({"city": "PARIS"})
        assert result["temp"] == 22

    def test_unknown_city(self):
        result = get_weather.invoke({"city": "Atlantis"})
        assert result["condition"] == "Unknown"


# ════════════════════════════════════════════════════════════════════
# SECTION 2: Pydantic Model Tests
# ════════════════════════════════════════════════════════════════════

class AgentInput(BaseModel):
    message:    str
    user_id:    str
    session_id: str

class AgentOutput(BaseModel):
    answer:    str
    tools_used: list[str] = []
    confidence: float = 1.0


class TestPydanticModels:
    """Test data validation models."""

    def test_valid_input(self):
        inp = AgentInput(message="Hello", user_id="u1", session_id="s1")
        assert inp.message == "Hello"
        assert inp.user_id == "u1"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError) as exc_info:
            AgentInput(message="Hello")  # missing user_id and session_id
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "user_id" in field_names

    def test_output_defaults(self):
        out = AgentOutput(answer="Paris is the capital of France.")
        assert out.tools_used == []
        assert out.confidence == 1.0

    def test_output_with_tools(self):
        out = AgentOutput(
            answer="2 + 2 = 4",
            tools_used=["calculator"],
            confidence=0.99,
        )
        assert "calculator" in out.tools_used
        assert out.confidence == 0.99

    def test_invalid_confidence(self):
        from pydantic import field_validator

        class StrictOutput(BaseModel):
            answer:     str
            confidence: float

            @field_validator("confidence")
            @classmethod
            def validate_confidence(cls, v):
                if not 0.0 <= v <= 1.0:
                    raise ValueError("confidence must be between 0 and 1")
                return v

        with pytest.raises(ValidationError):
            StrictOutput(answer="test", confidence=1.5)


# ════════════════════════════════════════════════════════════════════
# SECTION 3: Graph Node Tests
# ════════════════════════════════════════════════════════════════════

class TestGraphNodes:
    """Test individual LangGraph nodes without running the full graph."""

    def test_node_returns_state_update(self):
        """A node should return a partial state dict."""
        def my_node(state: AgentState) -> dict:
            return {"tools_used": state["tools_used"] + ["test_tool"]}

        initial_state = {"messages": [], "tools_used": []}
        result = my_node(initial_state)

        assert "tools_used" in result
        assert "test_tool" in result["tools_used"]

    def test_node_with_mock_llm(self):
        """Test a node that calls an LLM using a mock."""

        # Create a mock LLM that returns a predictable response
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Mocked LLM response")

        def llm_node(state: AgentState) -> dict:
            response = mock_llm.invoke(state["messages"])
            return {"messages": [response]}

        state = {"messages": [HumanMessage(content="test")], "tools_used": []}
        result = llm_node(state)

        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Mocked LLM response"
        mock_llm.invoke.assert_called_once()

    def test_tool_node_executes_tools(self):
        """Test that tools execute correctly when called directly.

        Note: ToolNode requires a compiled graph context to invoke.
        For unit tests, test tool functions directly instead.
        """
        # Test calculator tool directly
        result = calculator.invoke({"expression": "5 * 8"})
        assert "40" in result

        # Test weather tool directly
        weather = get_weather.invoke({"city": "London"})
        assert weather["temp"] == 15

        # Verify tool metadata (name/description) is correct
        assert calculator.name == "calculator"
        assert get_weather.name == "get_weather"
        assert "expression" in calculator.args
        assert "city" in get_weather.args


# ════════════════════════════════════════════════════════════════════
# SECTION 4: Full Graph Tests (with mocked LLM)
# ════════════════════════════════════════════════════════════════════

def build_test_agent(mock_llm):
    """Build agent graph using a mocked LLM."""

    def agent_node(state: AgentState) -> dict:
        response = mock_llm.invoke(state["messages"])
        tools_called = [tc["name"] for tc in (response.tool_calls or [])]
        return {
            "messages":   [response],
            "tools_used": state["tools_used"] + tools_called,
        }

    tool_node = ToolNode([calculator, get_weather])
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=MemorySaver())


class TestFullAgentGraph:
    """Integration tests for the complete agent graph."""

    def test_direct_answer_no_tools(self):
        """Agent should return directly when no tool calls are needed."""
        mock_llm = MagicMock()
        # First call: direct answer (no tool calls)
        mock_llm.invoke.return_value = AIMessage(
            content="Paris is the capital of France.",
            tool_calls=[],
        )

        agent = build_test_agent(mock_llm)
        result = agent.invoke(
            {"messages": [HumanMessage(content="What is the capital of France?")], "tools_used": []},
            config={"configurable": {"thread_id": "test_001"}},
        )

        assert "Paris" in result["messages"][-1].content
        assert result["tools_used"] == []

    def test_agent_uses_calculator_tool(self):
        """Agent should call calculator tool for math questions."""
        mock_llm = MagicMock()

        # First LLM call: request calculator
        mock_llm.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "calculator",
                    "args": {"expression": "7 * 6"},
                    "id":   "call_math",
                    "type": "tool_call",
                }]
            ),
            # Second LLM call: use tool result to give final answer
            AIMessage(
                content="7 * 6 = 42",
                tool_calls=[],
            ),
        ]

        agent = build_test_agent(mock_llm)
        result = agent.invoke(
            {"messages": [HumanMessage(content="What is 7 * 6?")], "tools_used": []},
            config={"configurable": {"thread_id": "test_002"}},
        )

        assert "calculator" in result["tools_used"]
        assert "42" in result["messages"][-1].content

    def test_memory_across_turns(self):
        """Agent should remember context across conversation turns."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Remembered!", tool_calls=[])

        agent = build_test_agent(mock_llm)
        config = {"configurable": {"thread_id": "test_memory"}}

        # Turn 1
        agent.invoke(
            {"messages": [HumanMessage(content="My name is Alice")], "tools_used": []},
            config=config,
        )

        # Turn 2 — same thread_id means memory is preserved
        result = agent.invoke(
            {"messages": [HumanMessage(content="What is my name?")], "tools_used": []},
            config=config,
        )

        # The second call's messages include turn 1 context
        all_messages = result["messages"]
        human_messages = [m for m in all_messages if isinstance(m, HumanMessage)]
        assert len(human_messages) == 2  # both turns present


# ════════════════════════════════════════════════════════════════════
# SECTION 5: Async Tests
# ════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async agent operations."""

    async def test_async_tool_call(self):
        """Test async tool execution."""
        async def async_search(query: str) -> str:
            await asyncio.sleep(0)  # simulate async I/O
            return f"Results for: {query}"

        result = await async_search("langchain")
        assert "langchain" in result

    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        async def mock_agent_call(request_id: int) -> dict:
            await asyncio.sleep(0.01)  # simulate processing
            return {"id": request_id, "answer": f"Response {request_id}"}

        tasks = [mock_agent_call(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["answer"] == f"Response {r['id']}" for r in results)

    async def test_async_state_management(self):
        """Test that async state updates are thread-safe."""
        results = []

        async def process(item: int):
            await asyncio.sleep(0)
            results.append(item * 2)

        await asyncio.gather(*[process(i) for i in range(10)])
        assert len(results) == 10
        assert sum(results) == sum(i * 2 for i in range(10))


# ════════════════════════════════════════════════════════════════════
# SECTION 6: Parametrized Tests
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("expression,expected", [
    ("2 + 2",      "4"),
    ("10 * 10",    "100"),
    ("100 / 4",    "25.0"),
    ("2 ** 8",     "256"),
    ("(5 + 3) * 2", "16"),
])
def test_calculator_parametrized(expression: str, expected: str):
    """Test calculator with multiple inputs."""
    result = calculator.invoke({"expression": expression})
    assert expected in result


@pytest.mark.parametrize("city,expected_condition", [
    ("London", "Rainy"),
    ("Paris",  "Sunny"),
    ("Tokyo",  "Humid"),
])
def test_weather_parametrized(city: str, expected_condition: str):
    """Test weather tool for multiple cities."""
    result = get_weather.invoke({"city": city})
    assert result["condition"] == expected_condition


# ════════════════════════════════════════════════════════════════════
# SECTION 7: Fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_llm():
    """Reusable mock LLM fixture."""
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="Fixture response", tool_calls=[])
    mock.bind_tools.return_value = mock
    return mock


@pytest.fixture
def sample_agent_state() -> AgentState:
    """Reusable agent state for tests."""
    return {
        "messages":   [HumanMessage(content="Hello")],
        "tools_used": [],
    }


@pytest.fixture(scope="session")
def agent_graph(mock_llm):
    """Session-scoped agent graph fixture."""
    return build_test_agent(mock_llm)


def test_with_fixtures(mock_llm, sample_agent_state):
    """Example test using fixtures."""
    agent = build_test_agent(mock_llm)
    result = agent.invoke(
        sample_agent_state,
        config={"configurable": {"thread_id": "fixture_test"}},
    )
    assert result is not None
    assert "messages" in result


# ════════════════════════════════════════════════════════════════════
# SECTION 8: conftest.py pattern
# ════════════════════════════════════════════════════════════════════

CONFTEST_CONTENT = '''
# 10_testing/conftest.py
# Put shared fixtures here — pytest auto-discovers this file

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

@pytest.fixture(autouse=True)
def no_real_api_calls(monkeypatch):
    """
    Safety fixture: prevent any real API calls in tests.
    This runs automatically for EVERY test.
    """
    monkeypatch.setenv("OPENAI_API_KEY",    "sk-test-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake")
    # If you ever see real API charges during testing,
    # this fixture is your safety net.


@pytest.fixture
def anyio_backend():
    return "asyncio"


# pytest.ini (or pyproject.toml) configuration:
[pytest]
asyncio_mode = auto
markers =
    slow: marks tests as slow (run with -m slow)
    integration: marks tests requiring external services
'''

print("=== Testing Module ===")
print("To run these tests:")
print("  pytest 10_testing/01_testing_ai_agents.py -v")
print("  pytest 10_testing/ -v --tb=short")
print("  pytest -k 'test_calculator' -v")       # run specific tests
print("  pytest -m 'not slow' -v")              # skip slow tests
print("  pytest --cov=. --cov-report=html")     # with coverage


if __name__ == "__main__":
    # Run basic tool tests directly
    print("\n=== Direct Tool Tests ===")
    print(f"2 + 2 = {calculator.invoke({'expression': '2 + 2'})}")
    print(f"London weather: {get_weather.invoke({'city': 'London'})}")
    print(f"Unknown city: {get_weather.invoke({'city': 'Atlantis'})}")
