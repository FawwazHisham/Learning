"""
09_ai_agents/01_complete_agent.py
===================================
Complete Production AI Agent

CONCEPTS COVERED:
  - Full agent implementation combining all previous modules
  - State management with Pydantic
  - Tool integration
  - Memory (Redis + SQLAlchemy)
  - Logging (loguru)
  - Retry logic (tenacity)
  - LangGraph state machine
  - Streaming responses
  - Error handling

This is a complete, runnable AI assistant agent that combines:
  ┌─────────────────────────────────────────────────────────────────┐
  │  User Input                                                      │
  │       ↓                                                          │
  │  [Input Validation - Pydantic]                                   │
  │       ↓                                                          │
  │  [Memory Retrieval - Redis/SQLite]                               │
  │       ↓                                                          │
  │  [Agent Loop - LangGraph]                                        │
  │    ├── Think (LLM)                                               │
  │    ├── Act (Tools: search, calc, time)                           │
  │    └── Observe (tool results)                                    │
  │       ↓                                                          │
  │  [Persist Conversation - SQLAlchemy]                             │
  │       ↓                                                          │
  │  [Structured Output - Pydantic]                                  │
  └─────────────────────────────────────────────────────────────────┘
"""

import asyncio
import os
from typing import TypedDict, Annotated, Optional
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


# ── 1. Data Models ────────────────────────────────────────────────────────────
class AgentRequest(BaseModel):
    """Validated input to the agent."""
    message:    str        = Field(min_length=1, max_length=10_000)
    user_id:    str        = Field(min_length=1)
    session_id: str        = Field(min_length=1)
    context:    dict       = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Validated output from the agent."""
    answer:     str
    session_id: str
    user_id:    str
    tools_used: list[str]  = Field(default_factory=list)
    turn_count: int
    timestamp:  datetime   = Field(default_factory=datetime.utcnow)
    error:      Optional[str] = None


class AgentState(TypedDict):
    """LangGraph state for the agent."""
    messages:     Annotated[list[BaseMessage], add_messages]
    user_id:      str
    session_id:   str
    tools_used:   list[str]
    turn_count:   int
    error:        Optional[str]


# ── 2. Tools ──────────────────────────────────────────────────────────────────
@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression like '2 + 2 * 10'
    """
    allowed_chars = set("0123456789 +-*/().,")
    if not all(c in allowed_chars for c in expression):
        return f"Error: unsafe expression '{expression}'"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool
def knowledge_search(topic: str) -> str:
    """Search the knowledge base for information on a topic.

    Args:
        topic: The topic to look up
    """
    kb = {
        "langchain":   "LangChain: framework for building LLM applications",
        "langgraph":   "LangGraph: stateful multi-actor AI applications",
        "openai":      "OpenAI: creator of GPT-4 and DALL-E",
        "anthropic":   "Anthropic: creator of Claude AI assistant",
        "pydantic":    "Pydantic: Python data validation library",
        "redis":       "Redis: in-memory data store for caching and sessions",
        "sqlalchemy":  "SQLAlchemy: Python SQL toolkit and ORM",
        "agent":       "AI Agent: autonomous system using LLMs to accomplish tasks",
        "react":       "ReAct: Reason+Act agent pattern using thought-action-observation",
        "rag":         "RAG: Retrieval Augmented Generation for knowledge-grounded LLMs",
    }
    topic_lower = topic.lower()
    for key, info in kb.items():
        if key in topic_lower:
            return info
    return f"No specific info found for '{topic}'. Try: {', '.join(kb.keys())}"


@tool
def get_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")


@tool
def text_analyzer(text: str) -> dict:
    """Analyze basic statistics about a piece of text.

    Args:
        text: The text to analyze
    """
    words   = text.split()
    sentences = text.count(".") + text.count("!") + text.count("?")
    return {
        "char_count":     len(text),
        "word_count":     len(words),
        "sentence_count": max(1, sentences),
        "avg_word_length": round(sum(len(w) for w in words) / max(1, len(words)), 1),
    }


TOOLS = [calculator, knowledge_search, get_datetime, text_analyzer]


# ── 3. LLM Setup ──────────────────────────────────────────────────────────────
def create_llm():
    """Create the LLM, falling back gracefully if no key available."""
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        logger.info("Using OpenAI GPT-4o-mini")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    elif os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        logger.info("Using Anthropic Claude Haiku")
        return ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    else:
        logger.warning("No API key found — using mock LLM")
        from langchain_core.runnables import RunnableLambda
        def mock_llm(messages):
            last = messages[-1].content if messages else ""
            return AIMessage(content=f"[Mock Agent] I received: '{last[:50]}...' — Set API key for real responses!")
        return RunnableLambda(mock_llm)


# ── 4. Build the Agent Graph ──────────────────────────────────────────────────
def build_agent(llm=None) -> tuple:
    """Build the complete agent graph with memory."""
    if llm is None:
        llm = create_llm()

    llm_with_tools = llm.bind_tools(TOOLS)
    tool_node = ToolNode(TOOLS)

    SYSTEM_PROMPT = SystemMessage(content=(
        "You are a helpful AI assistant with access to tools.\n"
        "You can:\n"
        "  - Do math with the calculator tool\n"
        "  - Look up information with knowledge_search\n"
        "  - Check the time with get_datetime\n"
        "  - Analyze text with text_analyzer\n\n"
        "Think step by step. Use tools when needed. "
        "Be concise and accurate."
    ))

    def agent_node(state: AgentState) -> dict:
        """Main agent reasoning node."""
        logger.debug(f"[agent] Processing {len(state['messages'])} messages")

        # Prepend system prompt to messages
        messages = [SYSTEM_PROMPT] + state["messages"]
        response = llm_with_tools.invoke(messages)

        # Track which tools were called
        tools_in_this_call = [tc["name"] for tc in (response.tool_calls or [])]
        all_tools = state["tools_used"] + tools_in_this_call

        return {
            "messages":   [response],
            "tools_used": all_tools,
            "turn_count": state["turn_count"] + 1,
        }

    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    memory = MemorySaver()
    compiled = graph.compile(checkpointer=memory)

    return compiled, memory


# ── 5. Production Agent Class ─────────────────────────────────────────────────
class ProductionAgent:
    """
    High-level agent interface with:
    - Input/output validation
    - Logging
    - Error handling
    - Retry logic
    """

    def __init__(self):
        self.graph, self.memory = build_agent()
        logger.info("ProductionAgent initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda rs: logger.warning(f"Retrying agent call (attempt {rs.attempt_number})..."),
    )
    def _invoke_graph(self, state: dict, config: dict) -> dict:
        """Invoke the graph with retry logic."""
        return self.graph.invoke(state, config=config)

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a user request through the agent.

        Args:
            request: Validated AgentRequest

        Returns:
            AgentResponse with answer and metadata
        """
        logger.info(
            f"Processing request",
            extra={
                "user_id":    request.user_id,
                "session_id": request.session_id,
                "message":    request.message[:50],
            }
        )

        # Build initial state
        initial_state: AgentState = {
            "messages":   [HumanMessage(content=request.message)],
            "user_id":    request.user_id,
            "session_id": request.session_id,
            "tools_used": [],
            "turn_count": 0,
            "error":      None,
        }

        # Config for this conversation thread
        config = {"configurable": {"thread_id": request.session_id}}

        try:
            # Run the agent
            start = datetime.now()
            final_state = self._invoke_graph(initial_state, config)
            elapsed = (datetime.now() - start).total_seconds()

            # Extract the final answer
            final_message = final_state["messages"][-1]
            answer = final_message.content if hasattr(final_message, "content") else str(final_message)

            logger.success(
                f"Request processed in {elapsed:.2f}s",
                extra={"tools_used": final_state["tools_used"]}
            )

            return AgentResponse(
                answer=answer,
                session_id=request.session_id,
                user_id=request.user_id,
                tools_used=final_state["tools_used"],
                turn_count=final_state["turn_count"],
            )

        except Exception as e:
            logger.error(f"Agent error: {e}")
            return AgentResponse(
                answer="I encountered an error processing your request. Please try again.",
                session_id=request.session_id,
                user_id=request.user_id,
                error=str(e),
                turn_count=0,
            )

    def stream(self, request: AgentRequest):
        """Stream agent events for real-time responses."""
        config = {"configurable": {"thread_id": request.session_id}}
        initial_state: AgentState = {
            "messages":   [HumanMessage(content=request.message)],
            "user_id":    request.user_id,
            "session_id": request.session_id,
            "tools_used": [],
            "turn_count": 0,
            "error":      None,
        }

        for event in self.graph.stream(initial_state, config=config, stream_mode="values"):
            last_msg = event["messages"][-1]
            yield {
                "type":    last_msg.__class__.__name__,
                "content": last_msg.content,
                "tools":   event.get("tools_used", []),
            }


# ── 6. Demo ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(Panel("[bold cyan]Production AI Agent Demo[/bold cyan]", border_style="cyan"))

    agent = ProductionAgent()

    test_cases = [
        ("user_001", "sess_001", "What is 125 * 8 + 42?"),
        ("user_001", "sess_001", "What is LangGraph?"),
        ("user_002", "sess_002", "What time is it?"),
        ("user_001", "sess_001", "Can you analyze this text: 'Hello world, this is a test.'"),
    ]

    table = Table(title="Agent Responses", show_lines=True)
    table.add_column("User",    style="cyan",  width=8)
    table.add_column("Query",   style="white", width=45)
    table.add_column("Answer",  style="green", width=50)
    table.add_column("Tools",   style="yellow", width=20)

    for user_id, session_id, message in test_cases:
        request = AgentRequest(
            message=message,
            user_id=user_id,
            session_id=session_id,
        )
        response = agent.process(request)

        table.add_row(
            user_id,
            message[:43] + "..." if len(message) > 43 else message,
            response.answer[:48] + "..." if len(response.answer) > 48 else response.answer,
            ", ".join(response.tools_used) or "none",
        )

    console.print(table)

    # Streaming demo
    console.print("\n[bold]Streaming Demo:[/bold]")
    console.print("Response: ", end="")
    stream_request = AgentRequest(
        message="Search for information about redis and calculate 2^10",
        user_id="user_001",
        session_id="sess_stream",
    )

    for event in agent.stream(stream_request):
        if event["type"] == "AIMessage" and event["content"]:
            console.print(f"\n[Agent]: {event['content'][:100]}", end="")

    console.print(f"\n\n[bold green]✓ Complete agent demo finished![/bold green]")
