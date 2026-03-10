"""
02_langchain_basics/04_tools_and_tool_calling.py
=================================================
LangChain: Tools & Tool Calling

CONCEPTS COVERED:
  - Defining tools with @tool decorator
  - Tool schema (name, description, args)
  - Binding tools to a model
  - Parsing tool calls from AIMessage
  - ToolExecutor — running tools
  - Tool calling loop (the ReAct pattern)
  - Structured tool args with Pydantic

The ReAct loop:
  User → Agent (think) → Tool call → Tool result → Agent (think) → ... → Answer
"""

import json
import math
import os
from typing import Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from pydantic import BaseModel, Field

load_dotenv()


# ── 1. Defining tools with @tool ──────────────────────────────────────────────
# The docstring IS the description — be specific and clear!
# The type hints define the schema that is sent to the model.

@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together. Use this for addition."""
    return a + b


@tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together. Use this for multiplication."""
    return a * b


@tool
def search_web(query: str) -> str:
    """Search the web for information. Use when you need current facts.

    Args:
        query: The search query to look up.
    """
    # In a real agent, this would call a search API
    results = {
        "langchain": "LangChain is a framework for building LLM applications.",
        "langgraph": "LangGraph builds stateful, multi-actor AI applications.",
        "python":    "Python is a high-level, general-purpose programming language.",
    }
    for key, value in results.items():
        if key in query.lower():
            return value
    return f"Search results for '{query}': [simulated result]"


@tool
def get_weather(city: str) -> dict:
    """Get the current weather for a city.

    Args:
        city: The name of the city to check weather for.
    """
    # Simulated weather data
    return {
        "city":        city,
        "temperature": 22,
        "condition":   "Sunny",
        "humidity":    65,
    }


# ── 2. Tools with complex Pydantic args ───────────────────────────────────────
class DatabaseQueryArgs(BaseModel):
    table:      str   = Field(description="The database table to query")
    conditions: str   = Field(description="SQL WHERE clause conditions", default="1=1")
    limit:      int   = Field(description="Max rows to return", default=10, ge=1, le=100)


@tool(args_schema=DatabaseQueryArgs)
def query_database(table: str, conditions: str = "1=1", limit: int = 10) -> list[dict]:
    """Query a database table with optional filtering.
    Use this to retrieve data from the application database.
    """
    # Simulated database response
    return [
        {"id": 1, "table": table, "conditions": conditions, "limit": limit},
    ]


# ── 3. Tool metadata — inspect tool definitions ───────────────────────────────
print("=== Tool Definitions ===")
for t in [add_numbers, search_web, get_weather]:
    print(f"\nTool    : {t.name}")
    print(f"Desc    : {t.description[:60]}")
    print(f"Schema  : {t.args}")


# ── 4. Binding tools to a model ───────────────────────────────────────────────
tools = [add_numbers, multiply_numbers, search_web, get_weather]
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model_with_tools = model.bind_tools(tools)


# ── 5. Making a tool call ─────────────────────────────────────────────────────
def demo_tool_call():
    print("\n=== Tool Call Demo ===")

    messages = [
        SystemMessage(content="You are a helpful assistant with access to tools."),
        HumanMessage(content="What is 42 multiplied by 13, then add 7?"),
    ]

    response: AIMessage = model_with_tools.invoke(messages)

    print(f"Content      : {response.content!r}")
    print(f"Tool calls   : {len(response.tool_calls)}")

    for tc in response.tool_calls:
        print(f"\n  Tool      : {tc['name']}")
        print(f"  Args      : {tc['args']}")
        print(f"  ID        : {tc['id']}")


# ── 6. Full tool execution loop ───────────────────────────────────────────────
def execute_tool_call(tool_call: dict) -> str:
    """Execute a tool and return the string result."""
    tool_map = {t.name: t for t in tools}
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    if tool_name not in tool_map:
        return f"Error: Tool '{tool_name}' not found"

    result = tool_map[tool_name].invoke(tool_args)
    return str(result)


def run_agent_loop(user_question: str, max_iterations: int = 10) -> str:
    """
    Implements the core ReAct agent loop:
    Think → Act (tool call) → Observe → Think → ... → Final answer
    """
    print(f"\n=== Agent Loop: '{user_question}' ===")

    messages = [
        SystemMessage(content=(
            "You are a helpful assistant. Use tools to answer questions. "
            "When you have the final answer, respond directly without calling any tools."
        )),
        HumanMessage(content=user_question),
    ]

    for iteration in range(max_iterations):
        print(f"\n[Iteration {iteration + 1}]")

        response = model_with_tools.invoke(messages)
        messages.append(response)

        # If no tool calls → model is done, return final answer
        if not response.tool_calls:
            print(f"Final Answer: {response.content}")
            return response.content

        # Execute each tool call and add results to messages
        for tool_call in response.tool_calls:
            print(f"  → Calling: {tool_call['name']}({tool_call['args']})")
            result = execute_tool_call(tool_call)
            print(f"  ← Result:  {result}")

            # ToolMessage must reference the tool_call_id
            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            ))

    return "Max iterations reached"


# ── 7. Tool error handling ────────────────────────────────────────────────────
@tool
def safe_divide(numerator: float, denominator: float) -> float:
    """Divide numerator by denominator.

    Args:
        numerator:   The number to divide.
        denominator: The number to divide by (cannot be zero).
    """
    if denominator == 0:
        raise ValueError("Cannot divide by zero")  # LangChain will catch and report
    return numerator / denominator


# ── 8. StructuredTool — for complex function signatures ───────────────────────
def complex_calculation(
    operation: str,
    operands: list[float],
    precision: int = 2,
) -> dict:
    """Perform a math operation on a list of numbers."""
    ops = {
        "sum":    sum,
        "max":    max,
        "min":    min,
        "mean":   lambda x: sum(x) / len(x),
        "product": math.prod,
    }
    if operation not in ops:
        return {"error": f"Unknown operation: {operation}"}

    result = ops[operation](operands)
    return {"operation": operation, "result": round(result, precision)}


calc_tool = StructuredTool.from_function(
    func=complex_calculation,
    name="complex_calculation",
    description=(
        "Perform a mathematical operation (sum/max/min/mean/product) "
        "on a list of numbers."
    ),
)


if __name__ == "__main__":
    print("\n=== Direct Tool Invocation ===")
    print(add_numbers.invoke({"a": 10, "b": 32}))      # 42.0
    print(get_weather.invoke({"city": "Tokyo"}))
    print(search_web.invoke({"query": "what is langgraph"}))

    if os.getenv("OPENAI_API_KEY"):
        demo_tool_call()
        run_agent_loop("What is 15 * 23? Then search for 'langchain'.")
    else:
        print("\nSet OPENAI_API_KEY in .env to run the full agent loop demos")
        print("\nKey concepts:")
        print("  @tool              → define a tool from a function")
        print("  model.bind_tools() → attach tools to a model")
        print("  AIMessage.tool_calls → the model's tool call requests")
        print("  ToolMessage        → the result of executing a tool")
