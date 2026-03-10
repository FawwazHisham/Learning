"""
06_langgraph_advanced/01_multi_agent.py
=========================================
LangGraph Advanced: Multi-Agent Systems

CONCEPTS COVERED:
  - Supervisor pattern: one agent routes to specialists
  - Subgraph composition: agents as graph nodes
  - Shared state vs private state
  - Agent handoffs
  - Parallel agent execution
  - Agent output aggregation

ARCHITECTURE:

  User → Supervisor → Research Agent → Supervisor → Writer Agent → Supervisor → User
                   ↑_____________________________________________↑

  The Supervisor decides which specialist to call and when to return to the user.
"""

from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv

load_dotenv()


# ── 1. Define shared state ────────────────────────────────────────────────────
class SupervisorState(TypedDict):
    """Shared state across all agents in the system."""
    messages:         Annotated[list[BaseMessage], add_messages]
    next_agent:       str       # which agent to call next
    research_results: list[str] # accumulated research
    draft_report:     str       # current draft
    final_report:     str       # completed report
    iterations:       int       # loop counter


# ── 2. Specialist agents ──────────────────────────────────────────────────────
def make_research_agent(llm):
    """Research agent: gathers information."""

    @tool
    def web_search(query: str) -> str:
        """Search the web for information."""
        # Simulate search results
        results = {
            "ai agents": "AI agents are autonomous systems that use LLMs to complete tasks.",
            "langchain":  "LangChain is a Python/JS framework for LLM application development.",
            "langgraph":  "LangGraph extends LangChain with stateful, cyclic computation graphs.",
        }
        for key in results:
            if key in query.lower():
                return results[key]
        return f"Research result for: {query}"

    @tool
    def read_document(url: str) -> str:
        """Read content from a URL."""
        return f"Document content from {url}: [detailed information about the topic]"

    research_tools = [web_search, read_document]
    llm_with_tools = llm.bind_tools(research_tools)

    def research_node(state: SupervisorState) -> dict:
        """Perform research based on the conversation."""
        print(f"[Research Agent] Starting research...")

        system = SystemMessage(content=(
            "You are a research specialist. Search for information and return key findings. "
            "Call search tools to find information, then summarize what you found."
        ))

        # Only use the last few messages for context
        recent_messages = state["messages"][-5:]
        response = llm_with_tools.invoke([system] + recent_messages)

        # Extract text content as research result
        research_text = response.content or "Research completed"
        print(f"[Research Agent] Found: {research_text[:60]}...")

        return {
            "messages":         [response],
            "research_results": state["research_results"] + [research_text],
            "next_agent":       "supervisor",  # always return to supervisor
            "iterations":       state["iterations"] + 1,
        }

    return research_node


def make_writer_agent(llm):
    """Writer agent: creates reports from research."""

    def writer_node(state: SupervisorState) -> dict:
        """Write a report based on accumulated research."""
        print(f"[Writer Agent] Writing report...")

        research = "\n".join(state["research_results"])
        system = SystemMessage(content=(
            "You are a technical writer. Create a clear, structured report "
            "from the provided research findings."
        ))
        human = HumanMessage(content=(
            f"Based on this research:\n{research}\n\n"
            f"Write a structured report for the user's question."
        ))

        response = llm.invoke([system, human])
        draft = response.content
        print(f"[Writer Agent] Draft: {draft[:60]}...")

        return {
            "messages":     [response],
            "draft_report": draft,
            "next_agent":   "supervisor",
            "iterations":   state["iterations"] + 1,
        }

    return writer_node


def make_reviewer_agent(llm):
    """Reviewer agent: quality-checks the report."""

    def reviewer_node(state: SupervisorState) -> dict:
        """Review and finalize the draft report."""
        print(f"[Reviewer Agent] Reviewing draft...")

        system = SystemMessage(content=(
            "You are a quality reviewer. Check the report for accuracy and clarity. "
            "Improve it if needed, then mark it as APPROVED."
        ))
        human = HumanMessage(content=f"Review this draft:\n\n{state['draft_report']}")

        response = llm.invoke([system, human])
        final = response.content
        print(f"[Reviewer Agent] Approved: {final[:60]}...")

        return {
            "messages":     [response],
            "final_report": final,
            "next_agent":   "END",  # reviewer is always last
            "iterations":   state["iterations"] + 1,
        }

    return reviewer_node


# ── 3. Supervisor node ────────────────────────────────────────────────────────
def make_supervisor(llm):
    """
    Supervisor: decides which agent to call next.
    This is the key node in the multi-agent pattern.
    """
    from pydantic import BaseModel

    class RouterDecision(BaseModel):
        next: Literal["research", "writer", "reviewer", "FINISH"]
        reason: str

    structured_llm = llm.with_structured_output(RouterDecision)

    def supervisor_node(state: SupervisorState) -> dict:
        """Route to the appropriate specialist agent."""
        print(f"[Supervisor] Deciding next step... (iteration {state['iterations']})")

        # Safety: prevent infinite loops
        if state["iterations"] >= 8:
            print("[Supervisor] Max iterations reached — finishing")
            return {"next_agent": "FINISH"}

        system_msg = SystemMessage(content=(
            "You are a supervisor managing a research team.\n"
            "Available agents:\n"
            "  - research: gather information from web/documents\n"
            "  - writer:   create a report from research findings\n"
            "  - reviewer: quality check and finalize the report\n"
            "  - FINISH:   return to user with final answer\n\n"
            "Workflow: research → (more research if needed) → writer → reviewer → FINISH\n"
            "Decide the NEXT agent to call."
        ))

        has_research = bool(state["research_results"])
        has_draft    = bool(state["draft_report"])
        has_final    = bool(state["final_report"])

        context = HumanMessage(content=(
            f"Current state:\n"
            f"  Research done: {has_research} ({len(state['research_results'])} results)\n"
            f"  Draft written: {has_draft}\n"
            f"  Review done:   {has_final}\n\n"
            f"Messages: {len(state['messages'])} total\n"
            f"What should happen next?"
        ))

        decision = structured_llm.invoke([system_msg, context])
        print(f"[Supervisor] Decision: {decision.next} — {decision.reason[:60]}")

        return {
            "next_agent": decision.next,
            "iterations": state["iterations"] + 1,
        }

    return supervisor_node


# ── 4. Build the multi-agent graph ────────────────────────────────────────────
def build_multi_agent_graph():
    """Build a supervisor-based multi-agent system."""
    from langchain_openai import ChatOpenAI
    from langchain_core.runnables import RunnableLambda

    if os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        # Mock LLM for demo
        llm = RunnableLambda(lambda _: AIMessage(content="[Mock response]"))
        # Mock structured output
        class MockStructured:
            def invoke(self, msgs):
                from pydantic import BaseModel
                class Decision(BaseModel):
                    next: str = "FINISH"
                    reason: str = "mock"
                return Decision()
            def bind_tools(self, tools):
                return self
        llm = MockStructured()

    graph = StateGraph(SupervisorState)

    # Add all nodes
    graph.add_node("supervisor", make_supervisor(llm))
    graph.add_node("research",   make_research_agent(llm))
    graph.add_node("writer",     make_writer_agent(llm))
    graph.add_node("reviewer",   make_reviewer_agent(llm))

    # Entry point
    graph.add_edge(START, "supervisor")

    # Conditional routing from supervisor
    def route_from_supervisor(state: SupervisorState) -> str:
        next_agent = state["next_agent"]
        if next_agent == "FINISH":
            return END
        return next_agent

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "research": "research",
            "writer":   "writer",
            "reviewer": "reviewer",
            END:        END,
        }
    )

    # All specialist agents return to supervisor
    graph.add_edge("research", "supervisor")
    graph.add_edge("writer",   "supervisor")
    graph.add_edge("reviewer", "supervisor")

    return graph.compile()


# ── 5. Run the multi-agent system ─────────────────────────────────────────────
print("=== Multi-Agent System ===")

multi_agent = build_multi_agent_graph()

initial_state = {
    "messages":         [HumanMessage(content="Write a report on what LangGraph is and why it matters.")],
    "next_agent":       "",
    "research_results": [],
    "draft_report":     "",
    "final_report":     "",
    "iterations":       0,
}

if os.getenv("OPENAI_API_KEY"):
    final_state = multi_agent.invoke(initial_state)
    print(f"\nFinal report ({len(final_state.get('final_report', ''))} chars):")
    print(final_state.get("final_report", "No report generated")[:500])
    print(f"\nTotal iterations: {final_state['iterations']}")
else:
    print("Set OPENAI_API_KEY to run the multi-agent system")
    print("\nArchitecture summary:")
    print("  Supervisor → Research → Supervisor → Writer → Supervisor → Reviewer → END")
    print("  The supervisor can loop research multiple times before writing")


# ── 6. Alternative: Parallel agents ───────────────────────────────────────────
"""
For tasks that can be parallelized, use Send() to fan out to multiple agents
simultaneously:

from langgraph.types import Send

def fan_out(state) -> list[Send]:
    # Send same task to multiple specialized agents in parallel
    return [
        Send("research_agent_1", {"query": state["query"], "source": "web"}),
        Send("research_agent_2", {"query": state["query"], "source": "database"}),
        Send("research_agent_3", {"query": state["query"], "source": "documents"}),
    ]

graph.add_conditional_edges("coordinator", fan_out)
# Results are collected in a reducer function
"""

print("\n=== Parallel Agents ===")
print("Use langgraph.types.Send to fan out to multiple agents simultaneously")
print("All results are collected via reducer functions in the state")
