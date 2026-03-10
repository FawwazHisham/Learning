"""
06_langgraph_advanced/02_memory_and_persistence.py
===================================================
LangGraph Advanced: Memory & Persistence

CONCEPTS COVERED:
  - MemorySaver: in-memory checkpoints (dev/testing)
  - SqliteSaver: file-based persistence
  - Thread-based sessions (thread_id)
  - State snapshots: get_state(), get_state_history()
  - Updating state externally (time travel / correction)
  - Short-term vs long-term memory patterns
  - External memory stores (vector DB for semantic search)

Why memory matters:
  Without persistence: every invocation starts fresh
  With persistence:    users can continue conversations
                       agents can remember context across sessions
                       you can debug/replay past runs
"""

import json
import os
from typing import TypedDict, Annotated, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()


# ── 1. State with persistent fields ───────────────────────────────────────────
class PersistentAgentState(TypedDict):
    """
    State designed for persistence across sessions.
    - messages: accumulates across turns (add_messages)
    - user_profile: remembered permanently
    - session_data: per-session context
    """
    messages:     Annotated[list[BaseMessage], add_messages]
    user_name:    str
    preferences:  dict        # user preferences remembered long-term
    session_id:   str
    turn_count:   int
    last_topic:   str         # what we last talked about


# ── 2. Simple chatbot with memory ─────────────────────────────────────────────
def build_memory_chatbot():
    """A chatbot that remembers across turns."""

    def chat_node(state: PersistentAgentState) -> dict:
        """Process user message and update state."""
        messages = state["messages"]
        last_human = messages[-1].content if messages else ""

        # Simple stateful logic
        turn = state["turn_count"] + 1
        name = state["user_name"] or "there"

        # Extract name if introduced
        if "my name is" in last_human.lower():
            words = last_human.lower().split("my name is")[-1].strip().split()
            name = words[0].capitalize() if words else name

        # Build response with memory
        if turn == 1:
            response_text = f"Hello, {name}! How can I help you today?"
        else:
            last_topic = state.get("last_topic", "")
            response_text = (
                f"Thanks {name}! You asked about: '{last_human[:50]}'. "
                f"This is turn {turn}."
                + (f" We were discussing {last_topic}." if last_topic else "")
            )

        return {
            "messages":   [AIMessage(content=response_text)],
            "user_name":  name,
            "turn_count": turn,
            "last_topic": last_human[:30],
        }

    graph = StateGraph(PersistentAgentState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    return graph


# ── 3. MemorySaver (in-memory, for development) ───────────────────────────────
print("=== MemorySaver (In-Memory) ===")

memory = MemorySaver()
chatbot = build_memory_chatbot().compile(checkpointer=memory)

# Thread ID = unique conversation session
config_alice = {"configurable": {"thread_id": "alice_session_001"}}
config_bob   = {"configurable": {"thread_id": "bob_session_001"}}

initial_state = {
    "messages":    [],
    "user_name":   "",
    "preferences": {},
    "session_id":  "alice_session_001",
    "turn_count":  0,
    "last_topic":  "",
}

# Alice's conversation
r1 = chatbot.invoke(
    {**initial_state, "messages": [HumanMessage(content="My name is Alice")]},
    config=config_alice,
)
print(f"Turn 1 (Alice): {r1['messages'][-1].content}")

r2 = chatbot.invoke(
    {"messages": [HumanMessage(content="What is LangGraph?")]},
    config=config_alice,  # same thread_id = same session
)
print(f"Turn 2 (Alice): {r2['messages'][-1].content}")

# Bob's separate conversation (different thread_id = separate memory)
r3 = chatbot.invoke(
    {**initial_state, "messages": [HumanMessage(content="Hi, I'm Bob")]},
    config=config_bob,
)
print(f"Turn 1 (Bob):   {r3['messages'][-1].content}")


# ── 4. Inspecting checkpointed state ──────────────────────────────────────────
print("\n=== State Inspection ===")

# Get current state of a thread
current_state = chatbot.get_state(config_alice)
print(f"Current turn count: {current_state.values['turn_count']}")
print(f"User name:          {current_state.values['user_name']}")
print(f"Total messages:     {len(current_state.values['messages'])}")

# Get state history (every checkpoint)
history = list(chatbot.get_state_history(config_alice))
print(f"Checkpoint count:   {len(history)}")
for i, checkpoint in enumerate(history[:3]):
    msg_count = len(checkpoint.values.get("messages", []))
    turn = checkpoint.values.get("turn_count", 0)
    print(f"  Checkpoint {i}: turn={turn}, messages={msg_count}")


# ── 5. SqliteSaver (file-based persistence) ───────────────────────────────────
"""
For production use SqliteSaver — checkpoints survive process restarts.

from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("./checkpoints.db") as saver:
    chatbot = build_memory_chatbot().compile(checkpointer=saver)

    # Now state persists between Python processes!
    result = chatbot.invoke(initial_state, config={"configurable": {"thread_id": "123"}})

# For async:
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
async with AsyncSqliteSaver.from_conn_string("./checkpoints.db") as saver:
    chatbot = build_memory_chatbot().compile(checkpointer=saver)
"""
print("\n=== SqliteSaver Pattern ===")
print("SqliteSaver: state persists across Python restarts")
print("Usage: SqliteSaver.from_conn_string('./checkpoints.db')")


# ── 6. Time travel: update state and replay ───────────────────────────────────
print("\n=== Time Travel: State Updates ===")

# Get a past checkpoint
history = list(chatbot.get_state_history(config_alice))
if len(history) >= 2:
    # Get the state from 2 turns ago
    past_checkpoint = history[-1]  # earliest checkpoint
    print(f"Past state (turn {past_checkpoint.values['turn_count']}): rewinding...")

    # Replay from that checkpoint (time travel!)
    replayed = chatbot.invoke(
        {"messages": [HumanMessage(content="Let me try a different question")]},
        config={**config_alice, "checkpoint_id": past_checkpoint.config["configurable"]["checkpoint_id"]},
    )
    print(f"Replayed from checkpoint: {replayed['messages'][-1].content[:60]}")


# ── 7. Long-term memory patterns ──────────────────────────────────────────────
"""
LangGraph's built-in memory (MemorySaver/SqliteSaver) is SHORT-TERM:
  - Stores the full message history for a thread
  - Perfect for conversation context within a session

For LONG-TERM memory (facts about users, knowledge bases):
  - Store in a database or vector store
  - Retrieve relevant memories at the start of each conversation

Pattern:
  1. At session start → query memory store for relevant facts
  2. Inject facts into system prompt
  3. At session end → extract new facts and store them
"""

class LongTermMemoryStore:
    """
    Simple in-memory store for demonstration.
    In production: use Redis, PostgreSQL, or a vector database.
    """
    def __init__(self):
        self._store: dict[str, dict] = {}

    def save_user_facts(self, user_id: str, facts: dict):
        """Save facts about a user."""
        self._store[user_id] = {
            **self._store.get(user_id, {}),
            **facts,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def get_user_facts(self, user_id: str) -> dict:
        """Retrieve all facts about a user."""
        return self._store.get(user_id, {})

    def get_context_for_prompt(self, user_id: str) -> str:
        """Format facts as a system prompt injection."""
        facts = self.get_user_facts(user_id)
        if not facts:
            return ""
        fact_lines = [f"  - {k}: {v}" for k, v in facts.items() if k != "updated_at"]
        return "What I know about this user:\n" + "\n".join(fact_lines)


# Demo long-term memory
ltm = LongTermMemoryStore()
ltm.save_user_facts("user_alice", {
    "name": "Alice",
    "role": "Data Scientist",
    "prefers_python": True,
    "expertise": "machine learning",
})

context = ltm.get_context_for_prompt("user_alice")
print("\n=== Long-Term Memory Context ===")
print(context)

# This would be injected at the start of each conversation:
system_with_memory = SystemMessage(content=(
    "You are a helpful AI assistant.\n\n"
    + context
))
print(f"\nSystem prompt with memory ({len(system_with_memory.content)} chars): built")


# ── 8. Memory architecture patterns ───────────────────────────────────────────
print("\n=== Memory Architecture Summary ===")
print("""
Memory Types:
  1. In-Context (messages list)
     - Everything in the current conversation window
     - Limited by model's context window (128k-200k tokens)
     - Fast, no retrieval needed

  2. Short-term (MemorySaver / SqliteSaver)
     - Full message history per thread_id
     - Survives session restarts with SqliteSaver
     - Good for multi-turn conversations

  3. Long-term (External store: Redis, PostgreSQL, vector DB)
     - User profiles, preferences, past interactions
     - Semantic search via embeddings (find relevant memories)
     - Scales to millions of users/conversations

  4. Episodic (Summarization)
     - Periodically summarize old messages
     - Keep recent messages + summary of older ones
     - Prevents context window overflow
""")
