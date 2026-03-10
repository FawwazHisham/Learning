"""
02_langchain_basics/02_prompt_templates.py
==========================================
LangChain: Prompt Templates

CONCEPTS COVERED:
  - PromptTemplate (simple string templates)
  - ChatPromptTemplate (for chat models)
  - MessagesPlaceholder (inject conversation history)
  - Partial templates (pre-fill some variables)
  - Few-shot prompting
  - Template composition and reuse
"""

from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
    FewShotChatMessagePromptTemplate,
)
from langchain_core.messages import HumanMessage, AIMessage


# ── 1. PromptTemplate — simple text templates ─────────────────────────────────
# Use {variable_name} for placeholders

basic_template = PromptTemplate.from_template(
    "Summarize the following text in {num_sentences} sentences:\n\n{text}"
)

# Format the template (returns a string, not a message)
formatted = basic_template.format(
    num_sentences=2,
    text="LangChain is a framework for developing applications powered by language models..."
)
print("=== PromptTemplate ===")
print(formatted)

# Get the input variable names
print(f"Variables: {basic_template.input_variables}")  # ['num_sentences', 'text']


# ── 2. ChatPromptTemplate — for chat models ───────────────────────────────────
# This is what you'll use 90% of the time

chat_template = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}. Your expertise is {domain}."),
    ("human",  "{question}"),
])

# format_messages() returns a list of BaseMessage objects
messages = chat_template.format_messages(
    role="senior software engineer",
    domain="distributed systems",
    question="What is the CAP theorem?",
)
print("\n=== ChatPromptTemplate ===")
for msg in messages:
    print(f"  [{msg.__class__.__name__}]: {msg.content}")


# ── 3. MessagesPlaceholder — inject conversation history ──────────────────────
# Essential for building chatbots with memory

chat_with_history = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="chat_history"),  # ← inject history here
    ("human",  "{input}"),
])

# Simulate a conversation history
history = [
    HumanMessage(content="My name is Alice."),
    AIMessage(content="Hello Alice! How can I help you?"),
    HumanMessage(content="What's the capital of France?"),
    AIMessage(content="The capital of France is Paris."),
]

messages_with_history = chat_with_history.format_messages(
    chat_history=history,
    input="What was my name again?",  # AI should remember from history
)
print("\n=== MessagesPlaceholder ===")
for msg in messages_with_history:
    print(f"  [{msg.__class__.__name__:12}]: {msg.content}")


# ── 4. Partial templates — pre-fill some variables ────────────────────────────
# Useful for creating specialized versions of a general template

general_analysis_template = ChatPromptTemplate.from_messages([
    ("system", "You are a {persona} analyzing {domain} content."),
    ("human",  "Analyze this: {content}"),
])

# Create a specialized version with persona fixed
security_analyzer = general_analysis_template.partial(
    persona="cybersecurity expert",
    domain="security vulnerability",
)

# Now only {content} needs to be provided
security_messages = security_analyzer.format_messages(
    content="The app stores passwords in plain text in a SQLite database."
)
print("\n=== Partial Template ===")
for msg in security_messages:
    print(f"  [{msg.__class__.__name__}]: {msg.content}")


# ── 5. Few-shot prompting — teach the model by example ────────────────────────
# Show the model input→output examples before the real question

examples = [
    {
        "input": "What is 2+2?",
        "output": "4"
    },
    {
        "input": "What is the capital of Germany?",
        "output": "Berlin"
    },
    {
        "input": "Who wrote Romeo and Juliet?",
        "output": "William Shakespeare"
    },
]

# Template for each example
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai",    "{output}"),
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
)

# Wrap in a full chat template
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise assistant. Give one-word answers."),
    few_shot_prompt,   # ← examples go here
    ("human", "{question}"),
])

formatted_few_shot = final_prompt.format_messages(question="What color is the sky?")
print("\n=== Few-Shot Prompting ===")
for msg in formatted_few_shot:
    print(f"  [{msg.__class__.__name__:12}]: {msg.content}")


# ── 6. Template reuse patterns ────────────────────────────────────────────────

class PromptLibrary:
    """Centralized store of reusable prompt templates."""

    SUMMARIZER = ChatPromptTemplate.from_messages([
        ("system", "Summarize the text in exactly {num_words} words."),
        ("human",  "{text}"),
    ])

    CODE_REVIEWER = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert {language} developer. "
            "Review the code for: bugs, security issues, and performance."
        )),
        ("human", "Review this code:\n\n```{language}\n{code}\n```"),
    ])

    AGENT_SYSTEM = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an AI agent with access to tools.\n"
            "Today's date: {date}\n"
            "Always think step by step before calling a tool."
        )),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])


# Show the structure of a template
print("\n=== Template Variables ===")
print(f"SUMMARIZER variables  : {PromptLibrary.SUMMARIZER.input_variables}")
print(f"CODE_REVIEWER variables: {PromptLibrary.CODE_REVIEWER.input_variables}")
print(f"AGENT_SYSTEM variables : {PromptLibrary.AGENT_SYSTEM.input_variables}")
