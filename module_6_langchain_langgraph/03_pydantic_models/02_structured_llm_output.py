"""
03_pydantic_models/02_structured_llm_output.py
===============================================
Pydantic + LangChain: Structured LLM Outputs

CONCEPTS COVERED:
  - model.with_structured_output() — the modern way
  - JsonOutputParser with Pydantic schema
  - PydanticOutputParser (older approach)
  - Retry on validation failure
  - OutputFixingParser — ask LLM to fix bad output
  - Real-world agent output schemas
"""

import os
from typing import Optional, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini", temperature=0) if os.getenv("OPENAI_API_KEY") else None


# ── 1. Define structured output schemas ──────────────────────────────────────

class TaskPlan(BaseModel):
    """An AI-generated plan for completing a task."""
    goal:        str               = Field(description="The main objective")
    steps:       list[str]         = Field(description="Ordered list of steps to achieve the goal")
    tools_needed: list[str]        = Field(description="Tools or resources required")
    estimated_complexity: Literal["low", "medium", "high"]
    risks:       list[str]         = Field(default_factory=list)

class CodeReview(BaseModel):
    """Structured code review from an AI assistant."""
    overall_rating:  int           = Field(ge=1, le=10, description="Quality score 1-10")
    bugs:            list[str]     = Field(default_factory=list)
    security_issues: list[str]     = Field(default_factory=list)
    improvements:    list[str]     = Field(default_factory=list)
    summary:         str

class EntityExtraction(BaseModel):
    """Entities extracted from a piece of text."""
    people:      list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    locations:   list[str] = Field(default_factory=list)
    dates:       list[str] = Field(default_factory=list)
    topics:      list[str] = Field(default_factory=list)

class RouterDecision(BaseModel):
    """Agent router's decision about next step."""
    next_agent:  str         = Field(description="Name of the agent to route to")
    reason:      str         = Field(description="Why this agent was chosen")
    confidence:  float       = Field(ge=0.0, le=1.0)
    fallback:    Optional[str] = Field(default=None, description="Fallback if primary fails")


# ── 2. model.with_structured_output() — BEST approach ────────────────────────
# This is the recommended modern approach. LangChain handles:
# - Adding JSON schema to the prompt
# - Parsing and validating the response
# - Automatic retries on parse failure

def demo_structured_output():
    if not model:
        print("No API key — showing structure only")
        print("Usage: model.with_structured_output(TaskPlan).invoke(messages)")
        return

    print("=== with_structured_output() ===")

    structured_model = model.with_structured_output(TaskPlan)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a project planner. Create detailed task plans."),
        ("human",  "Create a plan to: {task}"),
    ])

    chain = prompt | structured_model

    plan: TaskPlan = chain.invoke({
        "task": "Build a REST API for a book library system"
    })

    print(f"Goal       : {plan.goal}")
    print(f"Complexity : {plan.estimated_complexity}")
    print(f"Steps      : {len(plan.steps)}")
    for i, step in enumerate(plan.steps[:3], 1):
        print(f"  {i}. {step}")
    print(f"Tools      : {plan.tools_needed}")


# ── 3. JsonOutputParser with Pydantic schema ──────────────────────────────────
# Older but still useful — gives you control over the prompt

def demo_json_parser():
    if not model:
        print("No API key — showing structure only")
        return

    print("\n=== JsonOutputParser with schema ===")

    parser = JsonOutputParser(pydantic_object=EntityExtraction)

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Extract named entities from the text.\n"
            "{format_instructions}"
        )),
        ("human", "{text}"),
    ])

    chain = prompt | model | parser

    result = chain.invoke({
        "text": (
            "Apple CEO Tim Cook met with Elon Musk in San Francisco on "
            "January 15, 2025 to discuss AI regulation policies."
        ),
        "format_instructions": parser.get_format_instructions(),
    })

    print(f"People       : {result.get('people', [])}")
    print(f"Organizations: {result.get('organizations', [])}")
    print(f"Locations    : {result.get('locations', [])}")
    print(f"Dates        : {result.get('dates', [])}")


# ── 4. Safe parsing with fallback ─────────────────────────────────────────────
from pydantic import ValidationError
import json

def safe_structured_invoke(chain, inputs: dict, model_cls: type[BaseModel]) -> BaseModel | None:
    """
    Invoke a chain and safely parse the output.
    Returns None if parsing fails instead of crashing.
    """
    try:
        result = chain.invoke(inputs)
        if isinstance(result, dict):
            return model_cls.model_validate(result)
        return result
    except ValidationError as e:
        print(f"[WARN] Structured output validation failed: {e.error_count()} errors")
        return None
    except json.JSONDecodeError:
        print("[WARN] LLM returned invalid JSON")
        return None


# ── 5. Multi-schema routing ───────────────────────────────────────────────────
# Different schemas for different agent states

class SearchResult(BaseModel):
    query:   str
    results: list[str]
    found:   bool

class CalculationResult(BaseModel):
    expression: str
    answer:     float
    steps:      list[str]

class AgentResponse(BaseModel):
    """Top-level response that can contain different result types."""
    response_type: Literal["search", "calculation", "answer"]
    content:       str
    # Only one of these will be populated
    search_data:      Optional[SearchResult]      = None
    calculation_data: Optional[CalculationResult] = None


# ── 6. Schema for the entire agent state ─────────────────────────────────────
# This shows how Pydantic models describe your agent's data throughout execution

class AgentMemory(BaseModel):
    """What the agent remembers across turns."""
    user_name:     Optional[str]           = None
    conversation:  list[dict]              = Field(default_factory=list)
    retrieved_facts: list[str]            = Field(default_factory=list)
    pending_tasks: list[str]              = Field(default_factory=list)
    completed_tasks: list[str]            = Field(default_factory=list)

class AgentInput(BaseModel):
    """Validated input to the agent."""
    user_message: str = Field(min_length=1, max_length=10_000)
    session_id:   str = Field(min_length=1)
    user_id:      Optional[str] = None
    context:      dict = Field(default_factory=dict)

class AgentOutput(BaseModel):
    """Validated output from the agent."""
    response:    str
    session_id:  str
    tools_used:  list[str]  = Field(default_factory=list)
    sources:     list[str]  = Field(default_factory=list)
    confidence:  float      = Field(default=1.0, ge=0.0, le=1.0)
    follow_up:   Optional[str] = None  # suggested next question


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo_structured_output()
    demo_json_parser()

    # Show how schema-driven APIs work
    print("\n=== Schema-Driven API Example ===")

    # Create and validate input
    try:
        agent_input = AgentInput(
            user_message="What is LangGraph?",
            session_id="sess_123",
            user_id="user_42"
        )
        print(f"Valid input: {agent_input.user_message!r}")
    except ValidationError as e:
        print(f"Input validation failed: {e}")

    # Create and validate output
    output = AgentOutput(
        response="LangGraph is a framework for building stateful AI agents.",
        session_id="sess_123",
        tools_used=["search"],
        confidence=0.95,
        follow_up="Would you like to see a LangGraph example?"
    )
    print(f"Output: {output.model_dump_json(indent=2)}")
