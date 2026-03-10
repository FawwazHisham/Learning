"""
05_langgraph_basics/02_agent_with_tools.py
==========================================
LangGraph: Building an Agent with Tools

CONCEPTS COVERED:
  - The complete ReAct agent pattern in LangGraph
  - ToolNode — automatic tool execution
  - tools_condition — route to tools or END
  - Infinite loop prevention with iteration limits
  - Checkpointing (memory) with MemorySaver
  - Streaming agent events
  - Interrupting for human review (Human-in-the-Loop)

This is the CORE PATTERN for 90% of AI agents.
"""

import os
from typing import Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


# ── 1. Define the agent state ──────────────────────────────────────────────
class AgentState(TypedDict := __import__("typing").TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


from typing import TypedDict  # noqa: F811 — redeclare properly

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ── 2. Define tools ───────────────────────────────────────────────────────────
@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A math expression like '2 + 2' or '10 * 5 / 2'
    """
    try:
        # Safe eval — only allow math operations
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return f"Error: Invalid characters in expression"
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


@tool
def search(query: str) -> str:
    """Search for information on a topic.

    Args:
        query: The topic to search for
    """
    # Simulated knowledge base
    knowledge = {
        "langgraph":   "LangGraph builds stateful, multi-actor AI applications as graphs.",
        "langchain":   "LangChain is a framework for developing LLM-powered applications.",
        "python":      "Python is a high-level, interpreted, general-purpose language.",
        "openai":      "OpenAI created GPT-4, the powerful language model.",
        "anthropic":   "Anthropic created Claude, a helpful and safe AI assistant.",
        "agent":       "An AI agent perceives its environment and takes actions to achieve goals.",
        "lcel":        "LCEL (LangChain Expression Language) uses | to compose chains.",
    }
    query_lower = query.lower()
    for key, answer in knowledge.items():
        if key in query_lower:
            return answer
    return f"Found general info on '{query}': [simulated search result]"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


tools = [calculator, search, get_current_time]


# ── 3. Build the agent graph ──────────────────────────────────────────────────
def build_react_agent(use_anthropic: bool = False) -> StateGraph:
    """
    Build a ReAct agent using LangGraph's prebuilt helpers.

    Graph structure:
      START → agent_node → [tools_condition] → tool_node → agent_node → ...
                                            ↓ (no tool calls)
                                           END
    """
    # Choose model
    if use_anthropic and os.getenv("ANTHROPIC_API_KEY"):
        llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    elif os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        # Fallback mock
        from langchain_core.runnables import RunnableLambda
        from langchain_core.messages import AIMessage
        llm = RunnableLambda(lambda msgs: AIMessage(content="Mock: 42"))

    # Bind tools to the model
    llm_with_tools = llm.bind_tools(tools)

    # ─ Node functions ─────────────────────────────────────────────────────────
    def agent_node(state: AgentState) -> dict:
        """
        The "think" step: send messages to LLM.
        LLM either:
          a) returns a tool_call → we go to tool_node
          b) returns text answer → we go to END
        """
        print(f"[agent] Processing {len(state['messages'])} messages...")
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # ─ Build graph ────────────────────────────────────────────────────────────
    graph = StateGraph(AgentState)

    # ToolNode automatically:
    # - Extracts tool calls from AIMessage
    # - Executes each tool
    # - Wraps results in ToolMessage objects
    tool_node = ToolNode(tools)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")

    # tools_condition:
    # - If latest message has tool_calls → route to "tools"
    # - Otherwise → route to END
    graph.add_conditional_edges("agent", tools_condition)

    # After executing tools, always go back to agent
    graph.add_edge("tools", "agent")

    return graph


# ── 4. Compile WITHOUT memory (stateless) ─────────────────────────────────────
stateless_agent = build_react_agent().compile()

print("=== Stateless Agent ===")
if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
    result = stateless_agent.invoke({
        "messages": [HumanMessage(content="What is 25 * 4? Also, what is LangGraph?")]
    })
    final = result["messages"][-1].content
    print(f"Answer: {final}")
else:
    print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run the agent")


# ── 5. Compile WITH memory (stateful — multi-turn!) ───────────────────────────
# MemorySaver stores state in-memory (great for development)
# In production: use SqliteSaver or PostgresSaver

memory = MemorySaver()
stateful_agent = build_react_agent().compile(checkpointer=memory)

print("\n=== Stateful Agent (Multi-turn Memory) ===")
if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):

    # Each conversation needs a unique thread_id
    config = {"configurable": {"thread_id": "session_001"}}

    # Turn 1
    r1 = stateful_agent.invoke(
        {"messages": [HumanMessage(content="My favorite number is 42.")]},
        config=config,
    )
    print(f"Turn 1: {r1['messages'][-1].content}")

    # Turn 2 — agent REMEMBERS turn 1 because of checkpointing!
    r2 = stateful_agent.invoke(
        {"messages": [HumanMessage(content="What is my favorite number times 10?")]},
        config=config,
    )
    print(f"Turn 2: {r2['messages'][-1].content}")


# ── 6. Streaming agent events ─────────────────────────────────────────────────
def stream_agent_events(question: str):
    """Stream each event as the agent processes."""
    print(f"\n=== Streaming: '{question}' ===")

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("API key required for streaming")
        return

    for event in stateless_agent.stream(
        {"messages": [HumanMessage(content=question)]},
        stream_mode="values",  # stream full state after each node
    ):
        last_msg = event["messages"][-1]
        role = last_msg.__class__.__name__
        content = last_msg.content[:80] if last_msg.content else "[tool call]"
        print(f"  [{role}]: {content}...")

    # Alternative: stream individual updates
    # for node_name, update in stateless_agent.stream(..., stream_mode="updates"):
    #     print(f"Node '{node_name}' produced: {update}")


stream_agent_events("What time is it, and what is 100 / 4?")


# ── 7. Human-in-the-Loop (interrupt_before) ───────────────────────────────────
"""
interrupt_before tells the graph to PAUSE before executing a node.
The user can inspect state, modify it, then resume.

Use cases:
  - Review tool calls before execution (safety)
  - Approve agent actions (auditing)
  - Inject human feedback mid-execution
"""

memory2 = MemorySaver()
interrupted_agent = build_react_agent().compile(
    checkpointer=memory2,
    interrupt_before=["tools"],  # ← pause before executing any tool
)

print("\n=== Human-in-the-Loop Pattern ===")
print("(Showing structure — uncomment to run interactively)")

# # Usage pattern:
# config = {"configurable": {"thread_id": "human_review_001"}}
#
# # Agent thinks and creates tool calls, then STOPS
# state = interrupted_agent.invoke(
#     {"messages": [HumanMessage(content="Calculate 999 * 777")]},
#     config=config,
# )
#
# # Human can inspect the tool call
# last_msg = state["messages"][-1]
# print(f"Agent wants to call: {last_msg.tool_calls}")
#
# # Human approves → resume (None resumes from last checkpoint)
# final_state = interrupted_agent.invoke(None, config=config)
# print(f"Final: {final_state['messages'][-1].content}")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n=== LangGraph Agent Pattern Summary ===")
print("""
Graph: START → agent → [tools? YES → tool_node → agent] → END
                                  NO ↓
                                  END

Key classes:
  StateGraph(State)    → create the graph
  ToolNode(tools)      → auto-executes tool calls
  tools_condition      → routes to tools or END
  MemorySaver()        → in-memory checkpointing
  .compile()           → finalize the graph
  .invoke(state)       → run the graph
  .stream(state)       → stream events
""")
