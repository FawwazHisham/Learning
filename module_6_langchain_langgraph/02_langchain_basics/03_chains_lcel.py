"""
02_langchain_basics/03_chains_lcel.py
=======================================
LangChain: LCEL — LangChain Expression Language

CONCEPTS COVERED:
  - The | (pipe) operator: composing chains
  - RunnableSequence, RunnableParallel, RunnableBranch
  - Output parsers: StrOutputParser, JsonOutputParser
  - RunnablePassthrough (pass input unchanged)
  - RunnableLambda (wrap any function)
  - Streaming LCEL chains
  - Batching chains
  - Error handling in chains

LCEL mental model:
  chain = prompt | model | parser
  chain.invoke({"key": "value"})

  Input flows left → right through each component.
  Each component receives the output of the previous one.
"""

import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
)
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
    RunnableSequence,
)
from langchain_core.messages import AIMessage

load_dotenv()

# Setup model (use a mock if no key)
def get_model():
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # Fallback: a lambda that returns a fake AIMessage for demo purposes
    return RunnableLambda(lambda msgs: AIMessage(content="[Mock response]"))

model = get_model()


# ── 1. The simplest chain: prompt | model | parser ────────────────────────────
summarize_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a summarizer. Be concise."),
    ("human",  "Summarize in one sentence: {text}"),
])

# StrOutputParser: extracts .content from AIMessage → plain string
simple_chain = summarize_prompt | model | StrOutputParser()

# The input dict must match the template's variables
result = simple_chain.invoke({
    "text": "LangChain is a framework that helps developers build applications "
            "powered by large language models. It provides abstractions for "
            "prompts, models, chains, and agents."
})
print("=== Simple Chain ===")
print(f"Summary: {result}")


# ── 2. RunnablePassthrough — pass input through unchanged ─────────────────────
# Often used to add the original input alongside the model's response

passthrough_chain = (
    RunnableParallel({
        "original": RunnablePassthrough(),   # passes the raw input dict
        "summary": simple_chain,             # also runs the chain
    })
)

combined = passthrough_chain.invoke({
    "text": "Python is a high-level, interpreted programming language."
})
print("\n=== RunnableParallel with Passthrough ===")
print(f"Original input : {combined['original']}")
print(f"Summary        : {combined['summary']}")


# ── 3. RunnableParallel — run multiple chains simultaneously ──────────────────
# All branches receive the SAME input; results come back as a dict

analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze the sentiment of the text. Reply with: positive/negative/neutral"),
    ("human",  "{text}"),
])

keyword_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract 3 keywords from the text. Reply as comma-separated list."),
    ("human",  "{text}"),
])

parallel_chain = RunnableParallel(
    summary=simple_chain,
    sentiment=(analysis_prompt | model | StrOutputParser()),
    keywords=(keyword_prompt | model | StrOutputParser()),
)

analysis = parallel_chain.invoke({
    "text": "LangGraph is an incredible tool for building reliable AI agents!"
})
print("\n=== RunnableParallel (3 branches) ===")
print(f"Summary  : {analysis['summary']}")
print(f"Sentiment: {analysis['sentiment']}")
print(f"Keywords : {analysis['keywords']}")


# ── 4. JsonOutputParser — parse structured JSON responses ──────────────────────
json_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a data extractor. Always respond with valid JSON.\n"
        "Extract: name, age, skills (list) from the text."
    )),
    ("human", "{text}"),
])

json_chain = json_prompt | model | JsonOutputParser()

bio_text = "Alice is a 28-year-old software engineer who knows Python, Go, and Rust."
parsed = json_chain.invoke({"text": bio_text})
print("\n=== JsonOutputParser ===")
print(f"Extracted: {parsed}")
print(f"Name: {parsed.get('name', 'N/A')}, Skills: {parsed.get('skills', [])}")


# ── 5. RunnableLambda — wrap any Python function in LCEL ──────────────────────
def preprocess_text(input_dict: dict) -> dict:
    """Clean and normalize text before passing to LLM."""
    text = input_dict["text"]
    text = text.strip().lower().replace("\n", " ")
    return {"text": text, "char_count": len(text)}

def add_metadata(output: str) -> dict:
    """Add metadata to the final output."""
    return {
        "response": output,
        "word_count": len(output.split()),
        "has_code": "```" in output,
    }

enriched_chain = (
    RunnableLambda(preprocess_text)   # step 1: preprocess
    | simple_chain                    # step 2: summarize (uses "text" key)
    | RunnableLambda(add_metadata)    # step 3: add metadata
)

enriched_result = enriched_chain.invoke({
    "text": "   LANGCHAIN Is A Framework For LLM Applications.   "
})
print("\n=== RunnableLambda ===")
print(f"Response  : {enriched_result['response']}")
print(f"Word count: {enriched_result['word_count']}")


# ── 6. Streaming a chain ──────────────────────────────────────────────────────
def demo_streaming():
    print("\n=== Streaming Chain ===")
    print("Response: ", end="", flush=True)

    for chunk in simple_chain.stream({"text": "AI agents use LLMs to accomplish complex tasks."}):
        print(chunk, end="", flush=True)
    print()


# ── 7. Batching a chain ───────────────────────────────────────────────────────
def demo_batching():
    print("\n=== Batching Chain ===")

    inputs = [
        {"text": "Python is a programming language."},
        {"text": "Docker is a containerization platform."},
        {"text": "Redis is an in-memory data store."},
    ]

    # Processes all inputs concurrently
    results = simple_chain.batch(inputs, config={"max_concurrency": 3})

    for inp, result in zip(inputs, results):
        print(f"  Input : {inp['text'][:40]}")
        print(f"  Output: {result}\n")


# ── 8. Chain composition patterns ─────────────────────────────────────────────
# You can compose chains by chaining the pipe operators:

step1 = RunnableLambda(lambda x: {"text": x["raw_text"].upper()})
step2 = simple_chain
step3 = RunnableLambda(lambda s: {"final": s, "length": len(s)})

pipeline = step1 | step2 | step3

# This is equivalent to:
pipeline_explicit = RunnableSequence(first=step1, middle=[step2], last=step3)

print("\n=== Chain composition ===")
print("Chain created successfully: step1 | step2 | step3")
print(f"Chain type: {type(pipeline).__name__}")


if __name__ == "__main__":
    if os.getenv("OPENAI_API_KEY"):
        demo_streaming()
        demo_batching()
    else:
        print("\nSet OPENAI_API_KEY to run streaming and batching demos")

    print("\n✓ LCEL key takeaways:")
    print("  chain = prompt | model | parser  ← compose with pipe")
    print("  chain.invoke({'key': 'value'})   ← single call")
    print("  chain.stream({'key': 'value'})   ← token streaming")
    print("  chain.batch([dict, dict, ...])   ← parallel batch")
