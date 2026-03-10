"""
02_langchain_basics/01_models_and_messages.py
===============================================
LangChain: Chat Models & Messages

CONCEPTS COVERED:
  - ChatOpenAI and ChatAnthropic model setup
  - Message types: HumanMessage, AIMessage, SystemMessage
  - invoke() vs stream() vs batch()
  - Model parameters: temperature, max_tokens
  - Switching between providers transparently
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)

load_dotenv()

# ── 1. Creating Chat Models ───────────────────────────────────────────────────
# Both providers share the same LangChain interface — you can swap them freely

openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,          # 0 = deterministic, 1 = creative
    max_tokens=1024,
    api_key=os.getenv("OPENAI_API_KEY"),
)

anthropic_model = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0,
    max_tokens=1024,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# ── 2. Message Types — how to structure conversations ────────────────────────
# SystemMessage  → sets the AI's persona/behavior
# HumanMessage   → user's input
# AIMessage      → AI's past responses (for multi-turn history)

messages = [
    SystemMessage(content="You are a concise AI assistant. Answer in 1–2 sentences."),
    HumanMessage(content="What is LangChain?"),
]


# ── 3. invoke() — single synchronous call ─────────────────────────────────────
def demo_invoke():
    """Basic question-answer call."""
    print("\n=== invoke() demo ===")

    response: AIMessage = openai_model.invoke(messages)

    print(f"Content  : {response.content}")
    print(f"Type     : {type(response).__name__}")
    print(f"Model    : {response.response_metadata.get('model_name', 'unknown')}")
    print(f"Usage    : {response.usage_metadata}")


# ── 4. stream() — token-by-token streaming ────────────────────────────────────
def demo_stream():
    """Stream tokens as they arrive — great for responsive UIs."""
    print("\n=== stream() demo ===")
    print("Assistant: ", end="", flush=True)

    for chunk in openai_model.stream(messages):
        print(chunk.content, end="", flush=True)  # print each token as it arrives

    print()  # newline after streaming ends


# ── 5. batch() — process multiple prompts efficiently ─────────────────────────
def demo_batch():
    """Send multiple prompts in one call — better throughput."""
    print("\n=== batch() demo ===")

    batch_messages = [
        [HumanMessage(content="What is LangChain?")],
        [HumanMessage(content="What is LangGraph?")],
        [HumanMessage(content="What is an AI Agent?")],
    ]

    responses = openai_model.batch(batch_messages)  # runs concurrently

    for i, resp in enumerate(responses):
        print(f"Q{i+1}: {resp.content[:80]}...")


# ── 6. Multi-turn conversation ────────────────────────────────────────────────
def demo_multi_turn():
    """Build a conversation history manually."""
    print("\n=== Multi-turn conversation ===")

    history: list[BaseMessage] = [
        SystemMessage(content="You are a Python expert. Be brief."),
    ]

    questions = [
        "What is a list comprehension?",
        "Can you show me an example?",
        "How is it different from a generator expression?",
    ]

    for question in questions:
        history.append(HumanMessage(content=question))
        response = openai_model.invoke(history)
        history.append(response)  # add AI's reply to history
        print(f"\nQ: {question}")
        print(f"A: {response.content[:150]}...")


# ── 7. Provider-agnostic function ─────────────────────────────────────────────
def ask_any_model(
    question: str,
    provider: str = "openai",
    system: str = "You are a helpful assistant."
) -> str:
    """Use the same code regardless of provider."""
    model = openai_model if provider == "openai" else anthropic_model
    messages = [
        SystemMessage(content=system),
        HumanMessage(content=question),
    ]
    response = model.invoke(messages)
    return response.content


# ── 8. Model configuration options ───────────────────────────────────────────
"""
Common parameters for both ChatOpenAI and ChatAnthropic:

  temperature   float [0.0, 2.0]   creativity level (0=deterministic)
  max_tokens    int                 max response length in tokens
  timeout       float               seconds before giving up
  max_retries   int                 built-in retry count (also use tenacity!)
  streaming     bool                enable streaming mode by default

  # OpenAI-specific:
  model_kwargs  dict                extra params like response_format, seed

  # Anthropic-specific:
  top_k         int                 nucleus sampling parameter
  top_p         float               top-p sampling
"""

# Temperature guide:
#   0.0  → facts, code, structured output (always)
#   0.3  → balanced, most general use cases
#   0.7  → creative writing, brainstorming
#   1.0+ → very creative / unpredictable (rarely useful for agents)


if __name__ == "__main__":
    print("Checking API keys...")

    if os.getenv("OPENAI_API_KEY"):
        demo_invoke()
        demo_stream()
        demo_batch()
        demo_multi_turn()
    else:
        print("Set OPENAI_API_KEY in .env to run these demos")
        print("\nModel interface preview:")
        print("  model.invoke(messages)  → AIMessage")
        print("  model.stream(messages)  → Iterator[AIMessageChunk]")
        print("  model.batch([msgs,...]) → list[AIMessage]")

    # Always works (no API key needed to see the interface)
    print("\nProvider-agnostic call structure:")
    print("  ask_any_model('What is AI?', provider='openai')")
    print("  ask_any_model('What is AI?', provider='anthropic')")
