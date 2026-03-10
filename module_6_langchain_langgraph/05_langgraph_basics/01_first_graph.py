"""
05_langgraph_basics/01_first_graph.py
======================================
LangGraph: Your First State Machine Graph

CONCEPTS COVERED:
  - What is a graph in LangGraph?
  - StateGraph: the main class
  - State: TypedDict or Pydantic model
  - Nodes: functions that transform state
  - Edges: connections between nodes
  - Conditional edges: routing based on state
  - START and END special nodes
  - Compiling and invoking the graph
  - Visualizing the graph

MENTAL MODEL:
  LangGraph = a state machine where:
    - State  = the current data (passed node to node)
    - Nodes  = functions that transform the state
    - Edges  = the arrows between nodes
    - Graph  = the full blueprint

  Unlike a simple function chain, graphs can:
    - Loop back to earlier nodes
    - Branch to different nodes based on state
    - Run nodes in parallel
    - Pause and resume (checkpointing)
"""

from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# ── 1. Define the State ───────────────────────────────────────────────────────
# State is a TypedDict that every node reads from and writes to.
# Annotations control HOW values are updated:
#   - No annotation      → last writer wins (replace)
#   - Annotated[..., add_messages] → messages are APPENDED, not replaced

class SimpleState(TypedDict):
    """The simplest possible graph state."""
    input:   str
    output:  str
    step:    int


class ChatState(TypedDict):
    """State for a conversational agent."""
    messages: Annotated[list[BaseMessage], add_messages]  # ← messages ACCUMULATE
    user_name: str
    turn_count: int


# ── 2. Define Nodes ───────────────────────────────────────────────────────────
# A node is any function that:
#   - Takes the current State as input
#   - Returns a PARTIAL update to the state (only the keys you're changing)

def greet_node(state: SimpleState) -> dict:
    """First node: greets the user."""
    print(f"[greet_node] Input: {state['input']}")
    return {
        "output": f"Hello! You said: '{state['input']}'",
        "step":   state["step"] + 1,
    }


def process_node(state: SimpleState) -> dict:
    """Second node: processes the greeting."""
    print(f"[process_node] Step: {state['step']}")
    return {
        "output": state["output"].upper(),  # transform the output
        "step":   state["step"] + 1,
    }


def finalize_node(state: SimpleState) -> dict:
    """Final node: wraps up the response."""
    print(f"[finalize_node] Step: {state['step']}")
    return {
        "output": f"[DONE] {state['output']} (processed in {state['step']} steps)",
    }


# ── 3. Build the Graph ────────────────────────────────────────────────────────
def build_simple_graph() -> StateGraph:
    """Build a 3-node sequential graph."""

    graph = StateGraph(SimpleState)

    # Add nodes
    graph.add_node("greet",    greet_node)
    graph.add_node("process",  process_node)
    graph.add_node("finalize", finalize_node)

    # Add edges (connections between nodes)
    graph.add_edge(START,      "greet")    # ← START always needed
    graph.add_edge("greet",    "process")
    graph.add_edge("process",  "finalize")
    graph.add_edge("finalize", END)         # ← END always needed

    return graph


# ── 4. Compile and run ────────────────────────────────────────────────────────
simple_graph = build_simple_graph().compile()

print("=== Simple Sequential Graph ===")
result = simple_graph.invoke({
    "input": "hello world",
    "output": "",
    "step": 0,
})
print(f"Final output: {result['output']}")
print(f"Steps taken : {result['step']}")


# ── 5. Conditional Edges — branching logic ────────────────────────────────────
# The core of agent intelligence: choose WHICH node to go to next

class RoutingState(TypedDict):
    query:       str
    category:    str    # "math" | "general" | "code"
    answer:      str
    iterations:  int


def classify_query(state: RoutingState) -> dict:
    """Classify the query to route it to the right handler."""
    query = state["query"].lower()

    if any(word in query for word in ["calculate", "math", "number", "+", "-", "*", "/"]):
        category = "math"
    elif any(word in query for word in ["code", "python", "function", "class", "def"]):
        category = "code"
    else:
        category = "general"

    print(f"[classify] Query: '{state['query']}' → category: {category}")
    return {"category": category, "iterations": state["iterations"] + 1}


def math_handler(state: RoutingState) -> dict:
    """Handle math queries."""
    print(f"[math_handler] Handling: {state['query']}")
    return {"answer": f"Math answer for: {state['query']}"}


def code_handler(state: RoutingState) -> dict:
    """Handle code queries."""
    print(f"[code_handler] Handling: {state['query']}")
    return {"answer": f"Here's the code for: {state['query']}"}


def general_handler(state: RoutingState) -> dict:
    """Handle general queries."""
    print(f"[general_handler] Handling: {state['query']}")
    return {"answer": f"General answer: {state['query']}"}


def route_query(state: RoutingState) -> str:
    """
    Conditional edge function: returns the NAME of the next node.
    This is the 'router' — the brain of the branching.
    """
    return state["category"]  # "math", "code", or "general"


def build_routing_graph() -> StateGraph:
    graph = StateGraph(RoutingState)

    graph.add_node("classify",      classify_query)
    graph.add_node("math",          math_handler)
    graph.add_node("code",          code_handler)
    graph.add_node("general",       general_handler)

    graph.add_edge(START, "classify")

    # Conditional edge: after "classify", call route_query() to pick next node
    graph.add_conditional_edges(
        "classify",
        route_query,           # ← function that returns node name
        {                      # ← map from return value → node name
            "math":    "math",
            "code":    "code",
            "general": "general",
        }
    )

    # All handlers go to END
    graph.add_edge("math",    END)
    graph.add_edge("code",    END)
    graph.add_edge("general", END)

    return graph


routing_graph = build_routing_graph().compile()

print("\n=== Routing Graph ===")
for query in ["Calculate 2 + 2", "Write a Python function", "What is LangGraph?"]:
    result = routing_graph.invoke({"query": query, "category": "", "answer": "", "iterations": 0})
    print(f"  Q: {query!r:40} → Answer: {result['answer'][:40]}")


# ── 6. The add_messages annotation explained ──────────────────────────────────
"""
The add_messages annotation is crucial for chat agents.

WITHOUT add_messages (replace semantics):
    state["messages"] = [new_message]     # REPLACES all previous messages!

WITH add_messages (append semantics):
    state["messages"] += [new_message]    # APPENDS to existing messages ✓

This is how agents maintain conversation history automatically.
"""

def chat_node(state: ChatState) -> dict:
    """Add a simulated AI response to the conversation."""
    last_human = state["messages"][-1].content
    response = AIMessage(content=f"You said: '{last_human}'. I'm turn {state['turn_count'] + 1}.")
    return {
        "messages":    [response],         # add_messages will APPEND this
        "turn_count":  state["turn_count"] + 1,
    }


chat_graph_builder = StateGraph(ChatState)
chat_graph_builder.add_node("chat", chat_node)
chat_graph_builder.add_edge(START, "chat")
chat_graph_builder.add_edge("chat", END)
chat_graph = chat_graph_builder.compile()

print("\n=== Chat State with add_messages ===")
chat_state = {
    "messages":   [HumanMessage(content="Hello!")],
    "user_name":  "Alice",
    "turn_count": 0,
}
result = chat_graph.invoke(chat_state)
print(f"Messages in state: {len(result['messages'])}")
for msg in result["messages"]:
    print(f"  [{msg.__class__.__name__}]: {msg.content}")


# ── 7. Inspecting the graph ────────────────────────────────────────────────────
print("\n=== Graph Structure ===")
print(f"Routing graph nodes: {list(routing_graph.nodes.keys())}")
# To visualize as PNG: simple_graph.get_graph().draw_mermaid_png()
# To get Mermaid diagram: print(simple_graph.get_graph().draw_mermaid())
