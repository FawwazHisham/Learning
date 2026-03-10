"""
11_capstone_project/research_agent_system.py
=============================================
CAPSTONE: Production Research Agent System

A complete, multi-agent research assistant that:
  1. Receives a research question from the user
  2. Supervisor routes to specialist agents
  3. Research agent gathers facts using tools
  4. Analyst agent evaluates and structures findings
  5. Writer agent produces a polished report
  6. Returns structured output

Technologies integrated:
  ✓ LangGraph (state machine + multi-agent)
  ✓ LangChain (models, prompts, tools, LCEL)
  ✓ Pydantic v2 (input/output validation)
  ✓ loguru (structured logging)
  ✓ rich (beautiful terminal output)
  ✓ tenacity (retry logic)
  ✓ SQLAlchemy (persistence)
  ✓ MemorySaver (conversation memory)
  ✓ aiohttp/httpx patterns (async readiness)
"""

import os
import json
import time
from typing import TypedDict, Annotated, Literal, Optional
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage
)
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
console = Console()


# ══════════════════════════════════════════════════════════════════
# 1. DATA MODELS
# ══════════════════════════════════════════════════════════════════

class ResearchRequest(BaseModel):
    """Validated input to the research system."""
    question:   str = Field(min_length=5, max_length=2000, description="Research question")
    user_id:    str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    depth:      Literal["quick", "thorough"] = "thorough"
    format:     Literal["brief", "detailed", "bullet_points"] = "detailed"


class ResearchFinding(BaseModel):
    """A single research finding."""
    topic:      str
    summary:    str
    confidence: float = Field(ge=0.0, le=1.0)
    source:     str = "knowledge_base"


class ResearchReport(BaseModel):
    """Final output from the research system."""
    question:      str
    answer:        str
    key_findings:  list[ResearchFinding]
    sources:       list[str]
    tools_used:    list[str]
    session_id:    str
    generated_at:  datetime = Field(default_factory=datetime.utcnow)
    confidence:    float    = Field(ge=0.0, le=1.0, default=0.9)
    follow_ups:    list[str] = Field(default_factory=list)


class RouterDecision(BaseModel):
    """Supervisor's routing decision."""
    next:   Literal["researcher", "analyst", "writer", "FINISH"]
    reason: str


# ══════════════════════════════════════════════════════════════════
# 2. SHARED STATE
# ══════════════════════════════════════════════════════════════════

class ResearchState(TypedDict):
    """Full state passed between all agents."""
    # Core
    messages:      Annotated[list[BaseMessage], add_messages]
    question:      str
    user_id:       str
    session_id:    str

    # Research accumulation
    raw_findings:  list[dict]      # from researcher
    analysis:      str             # from analyst
    final_report:  str             # from writer
    sources:       list[str]

    # Control
    next_agent:    str
    iteration:     int
    tools_used:    list[str]
    errors:        list[str]


# ══════════════════════════════════════════════════════════════════
# 3. TOOLS
# ══════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    "langchain":    {
        "summary":    "LangChain is a Python/JavaScript framework for building LLM-powered apps.",
        "details":    "Provides: chains (LCEL), prompts, tools, agents, memory. Uses pipe operator.",
        "confidence": 0.98,
    },
    "langgraph":    {
        "summary":    "LangGraph builds stateful multi-actor AI applications as computation graphs.",
        "details":    "Built on LangChain. Key concepts: StateGraph, nodes, edges, checkpointing.",
        "confidence": 0.98,
    },
    "rag":          {
        "summary":    "RAG (Retrieval Augmented Generation) grounds LLM responses in external knowledge.",
        "details":    "Steps: embed documents → store in vector DB → retrieve relevant chunks → generate.",
        "confidence": 0.95,
    },
    "agent":        {
        "summary":    "AI agents use LLMs to reason and take actions in a loop until a goal is met.",
        "details":    "Patterns: ReAct, Plan-and-Execute, Supervisor, Swarm.",
        "confidence": 0.97,
    },
    "react":        {
        "summary":    "ReAct = Reason + Act. Agent alternates between thinking and calling tools.",
        "details":    "Yao et al. 2022. Observation-Thought-Action loop. Most common agent pattern.",
        "confidence": 0.96,
    },
    "pydantic":     {
        "summary":    "Pydantic provides Python data validation using type hints.",
        "details":    "v2 is 5-50x faster than v1. BaseModel, Field, validators, JSON schema.",
        "confidence": 0.97,
    },
    "redis":        {
        "summary":    "Redis is an in-memory key-value store for caching, sessions, and queues.",
        "details":    "Supports: strings, hashes, lists, sets, sorted sets, pub/sub, streams.",
        "confidence": 0.97,
    },
    "sqlalchemy":   {
        "summary":    "SQLAlchemy is the Python SQL toolkit and ORM.",
        "details":    "v2.0 uses mapped_column(), Mapped[], and select() queries. Supports async.",
        "confidence": 0.96,
    },
    "transformer":  {
        "summary":    "Transformer architecture: Attention is All You Need (Vaswani et al., 2017).",
        "details":    "Self-attention mechanism enables parallel processing and long-range dependencies.",
        "confidence": 0.95,
    },
    "vector database": {
        "summary":    "Stores high-dimensional vectors for semantic similarity search.",
        "details":    "Examples: Pinecone, Weaviate, Chroma, Qdrant. Essential for RAG systems.",
        "confidence": 0.94,
    },
}


@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information on a topic.

    Args:
        query: The topic or question to search for
    """
    query_lower = query.lower()
    results = []
    for key, data in KNOWLEDGE_BASE.items():
        if key in query_lower or any(w in query_lower for w in key.split()):
            results.append(f"[{key.upper()}] {data['summary']}\nDetails: {data['details']}")

    if results:
        return "\n\n".join(results[:3])  # return top 3 matches
    return f"No specific information found for '{query}' in knowledge base."


@tool
def analyze_text(text: str) -> dict:
    """Analyze text statistics and extract key information.

    Args:
        text: Text to analyze
    """
    words     = text.split()
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    # Simple keyword extraction
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to"}
    keywords = [w.lower().strip(".,!?") for w in words if w.lower() not in stop_words and len(w) > 4]
    unique_keywords = list(dict.fromkeys(keywords))[:10]

    return {
        "word_count":    len(words),
        "sentence_count": sentences,
        "reading_level": "intermediate" if len(words) / sentences > 15 else "simple",
        "key_terms":     unique_keywords,
        "summary_hint":  f"Text discusses: {', '.join(unique_keywords[:3])}" if unique_keywords else "general content",
    }


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression like '2 + 2' or '100 / 4'
    """
    safe_chars = set("0123456789+-*/()., ")
    if not all(c in safe_chars for c in expression):
        return f"Error: invalid characters in '{expression}'"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_current_date() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")


RESEARCH_TOOLS = [search_knowledge_base, analyze_text, calculate, get_current_date]


# ══════════════════════════════════════════════════════════════════
# 4. LLM SETUP
# ══════════════════════════════════════════════════════════════════

def get_llm(smart: bool = False):
    """Get the LLM (real or mock)."""
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        model = "gpt-4o" if smart else "gpt-4o-mini"
        return ChatOpenAI(model=model, temperature=0)
    elif os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        model = "claude-sonnet-4-6" if smart else "claude-haiku-4-5-20251001"
        return ChatAnthropic(model=model, temperature=0)
    else:
        from langchain_core.runnables import RunnableLambda

        def mock_response(msgs):
            # Smart mock that provides plausible responses
            last_msg = msgs[-1] if msgs else None
            content = getattr(last_msg, "content", "")

            if "route" in str(msgs[0].content if msgs else "").lower():
                return AIMessage(content=json.dumps({"next": "FINISH", "reason": "mock"}))
            elif "research" in content.lower() or "search" in content.lower():
                return AIMessage(
                    content="Based on my research, LangGraph is a powerful framework.",
                    tool_calls=[],
                )
            elif "analyz" in content.lower():
                return AIMessage(content="Analysis: The topic covers key AI agent concepts.")
            elif "report" in content.lower() or "write" in content.lower():
                return AIMessage(content=(
                    "# Research Report\n\n"
                    "## Answer\nLangGraph is a framework for building stateful AI agents.\n\n"
                    "## Key Points\n- State machines for agent control\n"
                    "- Multi-agent coordination\n- Persistent checkpointing\n\n"
                    "*[Mock report — set OPENAI_API_KEY for real responses]*"
                ))
            return AIMessage(content="[Mock LLM response — set OPENAI_API_KEY for real responses]")

        mock = RunnableLambda(mock_response)
        mock.bind_tools = lambda tools: mock  # no-op for mock
        return mock


# ══════════════════════════════════════════════════════════════════
# 5. AGENT NODES
# ══════════════════════════════════════════════════════════════════

def make_supervisor_node(llm):
    """Supervisor decides which agent to call next."""

    def supervisor(state: ResearchState) -> dict:
        logger.debug(f"[Supervisor] Iteration {state['iteration']}: deciding next step")

        if state["iteration"] >= 6:  # safety limit
            logger.warning("[Supervisor] Max iterations — finishing")
            return {"next_agent": "FINISH", "iteration": state["iteration"] + 1}

        has_findings  = bool(state["raw_findings"])
        has_analysis  = bool(state["analysis"])
        has_report    = bool(state["final_report"])

        # Simple rule-based routing (or use LLM for complex cases)
        if has_report:
            next_step = "FINISH"
        elif has_analysis:
            next_step = "writer"
        elif has_findings:
            next_step = "analyst"
        else:
            next_step = "researcher"

        logger.info(f"[Supervisor] Routing to: {next_step}")
        return {
            "next_agent": next_step,
            "iteration":  state["iteration"] + 1,
        }

    return supervisor


def make_researcher_node(llm):
    """Researcher gathers information using tools."""
    llm_with_tools = llm.bind_tools(RESEARCH_TOOLS)

    def researcher(state: ResearchState) -> dict:
        logger.info("[Researcher] Gathering information...")

        system = SystemMessage(content=(
            "You are a thorough research specialist. "
            "Use the search_knowledge_base tool to find relevant information. "
            "Search for all relevant aspects of the question. "
            "Be comprehensive — search multiple related terms."
        ))
        human = HumanMessage(content=f"Research this question: {state['question']}")

        response = llm_with_tools.invoke([system, human])

        # Extract tool calls and execute them manually for finding tracking
        findings = []
        tools_called = []

        if response.tool_calls:
            for tc in response.tool_calls:
                tools_called.append(tc["name"])
                tool_map = {t.name: t for t in RESEARCH_TOOLS}
                if tc["name"] in tool_map:
                    result = tool_map[tc["name"]].invoke(tc["args"])
                    findings.append({
                        "tool":    tc["name"],
                        "query":   tc["args"],
                        "result":  str(result),
                    })
                    logger.debug(f"[Researcher] Tool {tc['name']}: found {len(str(result))} chars")

        # If no tool calls, extract content as a finding
        if not findings and response.content:
            findings.append({
                "tool":   "direct_knowledge",
                "query":  {"question": state["question"]},
                "result": response.content,
            })

        logger.success(f"[Researcher] Found {len(findings)} results using {tools_called}")

        return {
            "messages":    [response],
            "raw_findings": state["raw_findings"] + findings,
            "tools_used":  state["tools_used"] + tools_called,
            "sources":     state["sources"] + ["knowledge_base"],
            "next_agent":  "supervisor",
        }

    return researcher


def make_analyst_node(llm):
    """Analyst structures and evaluates research findings."""

    def analyst(state: ResearchState) -> dict:
        logger.info("[Analyst] Analyzing findings...")

        findings_text = "\n\n".join([
            f"Finding {i+1} (via {f['tool']}):\n{f['result']}"
            for i, f in enumerate(state["raw_findings"])
        ])

        system = SystemMessage(content=(
            "You are an expert analyst. Given research findings, you:\n"
            "1. Identify the most relevant information\n"
            "2. Note any gaps or contradictions\n"
            "3. Structure insights clearly\n"
            "4. Rate confidence in the findings\n"
            "Be concise and objective."
        ))
        human = HumanMessage(content=(
            f"Question: {state['question']}\n\n"
            f"Research Findings:\n{findings_text}\n\n"
            f"Provide a structured analysis."
        ))

        response = llm.invoke([system, human])
        analysis = response.content

        logger.success(f"[Analyst] Analysis complete ({len(analysis)} chars)")

        return {
            "messages":  [response],
            "analysis":  analysis,
            "next_agent": "supervisor",
        }

    return analyst


def make_writer_node(llm):
    """Writer creates the final polished report."""

    def writer(state: ResearchState) -> dict:
        logger.info("[Writer] Writing final report...")

        system = SystemMessage(content=(
            "You are a technical writer. Create a clear, well-structured report.\n"
            "Format:\n"
            "  ## Answer\n  [Direct answer to the question]\n\n"
            "  ## Key Findings\n  [Bullet points of main findings]\n\n"
            "  ## Details\n  [Expanded explanation]\n\n"
            "  ## Follow-up Questions\n  [2-3 related questions to explore]\n\n"
            "Be accurate, clear, and helpful."
        ))
        human = HumanMessage(content=(
            f"Question: {state['question']}\n\n"
            f"Analysis:\n{state['analysis']}\n\n"
            f"Write the final research report."
        ))

        response = llm.invoke([system, human])
        report = response.content

        logger.success(f"[Writer] Report complete ({len(report)} chars)")

        return {
            "messages":     [response],
            "final_report": report,
            "next_agent":   "supervisor",
        }

    return writer


# ══════════════════════════════════════════════════════════════════
# 6. BUILD THE GRAPH
# ══════════════════════════════════════════════════════════════════

def build_research_system() -> tuple:
    llm = get_llm(smart=False)  # use smart=True for complex research

    graph = StateGraph(ResearchState)

    graph.add_node("supervisor",  make_supervisor_node(llm))
    graph.add_node("researcher",  make_researcher_node(llm))
    graph.add_node("analyst",     make_analyst_node(llm))
    graph.add_node("writer",      make_writer_node(llm))

    graph.add_edge(START, "supervisor")

    def route(state: ResearchState) -> str:
        next_agent = state["next_agent"]
        if next_agent == "FINISH":
            return END
        return next_agent

    graph.add_conditional_edges(
        "supervisor",
        route,
        {"researcher": "researcher", "analyst": "analyst", "writer": "writer", END: END},
    )

    graph.add_edge("researcher", "supervisor")
    graph.add_edge("analyst",    "supervisor")
    graph.add_edge("writer",     "supervisor")

    memory = MemorySaver()
    return graph.compile(checkpointer=memory), memory


# ══════════════════════════════════════════════════════════════════
# 7. HIGH-LEVEL INTERFACE
# ══════════════════════════════════════════════════════════════════

class ResearchAgentSystem:
    """High-level interface to the research agent system."""

    def __init__(self):
        self.graph, self.memory = build_research_system()
        logger.info("ResearchAgentSystem initialized")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=5),
    )
    def research(self, request: ResearchRequest) -> ResearchReport:
        """Execute a research request."""
        logger.info(f"Research request: {request.question!r}")

        initial_state: ResearchState = {
            "messages":     [HumanMessage(content=request.question)],
            "question":     request.question,
            "user_id":      request.user_id,
            "session_id":   request.session_id,
            "raw_findings": [],
            "analysis":     "",
            "final_report": "",
            "sources":      [],
            "next_agent":   "",
            "iteration":    0,
            "tools_used":   [],
            "errors":       [],
        }

        config = {"configurable": {"thread_id": request.session_id}}

        start_time = time.perf_counter()
        final_state = self.graph.invoke(initial_state, config=config)
        elapsed = time.perf_counter() - start_time

        logger.success(f"Research complete in {elapsed:.2f}s")

        # Parse follow-up questions from the report
        follow_ups = []
        report_text = final_state.get("final_report", "")
        if "Follow-up" in report_text or "follow-up" in report_text:
            lines = report_text.split("\n")
            in_followup = False
            for line in lines:
                if "follow" in line.lower() and "?" not in line:
                    in_followup = True
                elif in_followup and line.strip().startswith(("-", "•", "*", "1", "2", "3")):
                    q = line.strip().lstrip("-•*123. ")
                    if "?" in q:
                        follow_ups.append(q)

        return ResearchReport(
            question=request.question,
            answer=final_state.get("final_report", "No report generated"),
            key_findings=[
                ResearchFinding(
                    topic=f["tool"],
                    summary=str(f["result"])[:200],
                    confidence=0.9,
                    source=f["tool"],
                )
                for f in final_state.get("raw_findings", [])[:5]
            ],
            sources=list(set(final_state.get("sources", []))),
            tools_used=list(set(final_state.get("tools_used", []))),
            session_id=request.session_id,
            follow_ups=follow_ups[:3],
        )


# ══════════════════════════════════════════════════════════════════
# 8. DEMO
# ══════════════════════════════════════════════════════════════════

def run_demo():
    console.print(Panel(
        "[bold cyan]Research Agent System — Capstone Demo[/bold cyan]\n"
        "A multi-agent AI research assistant powered by LangGraph",
        border_style="cyan",
        expand=False,
    ))

    system = ResearchAgentSystem()

    questions = [
        "What is LangGraph and how does it relate to LangChain?",
        "How do AI agents work using the ReAct pattern?",
        "What is RAG and when should I use a vector database?",
    ]

    for i, question in enumerate(questions, 1):
        console.print(f"\n[bold yellow]Question {i}:[/bold yellow] {question}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Researching...", total=None)

            request = ResearchRequest(
                question=question,
                user_id="demo_user",
                session_id=f"demo_session_{i:03d}",
            )
            report = system.research(request)
            progress.stop()

        # Display results
        console.print(Panel(
            report.answer[:600] + ("..." if len(report.answer) > 600 else ""),
            title=f"[green]Research Report {i}[/green]",
            border_style="green",
        ))

        # Metadata table
        meta_table = Table(show_header=False, box=None)
        meta_table.add_column(style="cyan", width=15)
        meta_table.add_column(style="white")
        meta_table.add_row("Tools used", ", ".join(report.tools_used) or "none")
        meta_table.add_row("Sources",    ", ".join(report.sources) or "none")
        meta_table.add_row("Findings",   str(len(report.key_findings)))
        meta_table.add_row("Generated",  report.generated_at.strftime("%H:%M:%S"))

        if report.follow_ups:
            meta_table.add_row("Follow-ups", "\n".join(f"• {q}" for q in report.follow_ups))

        console.print(meta_table)

    console.print(Panel(
        "[bold green]✓ Research Agent System demo complete![/bold green]\n\n"
        "Technologies used:\n"
        "  • LangGraph: multi-agent state machine\n"
        "  • LangChain: tools, prompts, models\n"
        "  • Pydantic: input/output validation\n"
        "  • loguru: structured logging\n"
        "  • rich: beautiful output\n"
        "  • tenacity: retry logic\n"
        "  • MemorySaver: conversation persistence",
        border_style="green",
    ))


if __name__ == "__main__":
    run_demo()
