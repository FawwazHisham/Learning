"""
03_pydantic_models/01_pydantic_v2_basics.py
============================================
Pydantic v2: Data Validation for AI Outputs

CONCEPTS COVERED:
  - BaseModel: defining typed data classes
  - Field: validation, defaults, descriptions
  - Validators: @field_validator, @model_validator
  - Nested models
  - Model serialization: .model_dump(), .model_json_schema()
  - Strict vs lax mode
  - AI-specific patterns: parsing LLM outputs safely

Why Pydantic for AI?
  LLMs output text. You need to parse that text into structured data.
  Pydantic validates the structure and catches hallucinations/errors.
"""

from __future__ import annotations
import json
from typing import Optional, Literal
from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ValidationError,
    ConfigDict,
)


# ── 1. Basic BaseModel ────────────────────────────────────────────────────────
class User(BaseModel):
    id:    int
    name:  str
    email: str
    age:   int

# Create from dict
user = User(id=1, name="Alice", email="alice@example.com", age=30)
print("=== Basic Model ===")
print(user)
print(f"Name: {user.name}, Age: {user.age}")

# Pydantic coerces types automatically (lax mode by default)
user2 = User(id="42", name="Bob", email="bob@example.com", age="25")  # str → int
print(f"Coerced id: {user2.id} (type: {type(user2.id).__name__})")


# ── 2. Field — validation and metadata ───────────────────────────────────────
class AgentConfig(BaseModel):
    name:         str        = Field(min_length=1, max_length=100, description="Agent name")
    model:        str        = Field(default="gpt-4o-mini", description="LLM model ID")
    temperature:  float      = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens:   int        = Field(default=1024, ge=1, le=100_000)
    system_prompt: str       = Field(default="You are a helpful assistant.")
    tools:        list[str]  = Field(default_factory=list)
    tags:         list[str]  = Field(default_factory=list, max_length=10)

    model_config = ConfigDict(
        str_strip_whitespace=True,  # strip leading/trailing spaces from strings
        extra="forbid",             # reject unknown fields
    )

config = AgentConfig(name="ResearchAgent", temperature=0.3, tools=["search", "calculator"])
print("\n=== AgentConfig with Field ===")
print(config.model_dump())


# ── 3. @field_validator — custom field validation ─────────────────────────────
class EmailModel(BaseModel):
    email: str
    username: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError(f"'{v}' is not a valid email address")
        return v.lower().strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must contain only letters and numbers")
        return v.lower()

try:
    valid_user = EmailModel(email="  Alice@Example.COM  ", username="Alice123")
    print(f"\n=== Field Validator ===")
    print(f"Email: {valid_user.email}")     # alice@example.com
    print(f"Username: {valid_user.username}")  # alice123
except ValidationError as e:
    print(f"Validation error: {e}")


# ── 4. @model_validator — cross-field validation ──────────────────────────────
class DateRange(BaseModel):
    start_date: datetime
    end_date:   datetime
    label:      str = "untitled"

    @model_validator(mode="after")
    def check_date_order(self) -> "DateRange":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


# ── 5. Nested models — LLM output structures ─────────────────────────────────
class ResearchSource(BaseModel):
    url:       str
    title:     str
    relevance: float = Field(ge=0.0, le=1.0)

class ResearchReport(BaseModel):
    query:     str
    summary:   str
    sources:   list[ResearchSource]
    confidence: float = Field(ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_used:   str = "unknown"

    @model_validator(mode="after")
    def check_sources_not_empty(self) -> "ResearchReport":
        if not self.sources:
            raise ValueError("Research report must have at least one source")
        return self

# Simulate parsing an LLM's JSON output
llm_output_json = """
{
    "query": "What is LangGraph?",
    "summary": "LangGraph is a library for building stateful, multi-actor AI applications.",
    "sources": [
        {"url": "https://langchain.com/langgraph", "title": "LangGraph Docs", "relevance": 0.95},
        {"url": "https://github.com/langchain-ai/langgraph", "title": "LangGraph GitHub", "relevance": 0.88}
    ],
    "confidence": 0.92,
    "model_used": "gpt-4o-mini"
}
"""

print("\n=== Nested Models (LLM Output Parsing) ===")
try:
    report = ResearchReport.model_validate_json(llm_output_json)
    print(f"Query     : {report.query}")
    print(f"Summary   : {report.summary[:60]}...")
    print(f"Sources   : {len(report.sources)} found")
    print(f"Confidence: {report.confidence:.0%}")
except ValidationError as e:
    print(f"LLM output failed validation:\n{e}")


# ── 6. Structured AI output with Literal types ────────────────────────────────
class ClassificationResult(BaseModel):
    """Parse LLM classification outputs."""
    text:       str
    category:   Literal["question", "command", "statement", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning:  str   = Field(min_length=10)

class SentimentResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    score:     float  = Field(ge=-1.0, le=1.0, description="-1=very negative, 1=very positive")
    emotion:   Optional[str] = None


# ── 7. Handling validation errors gracefully ──────────────────────────────────
def safe_parse_llm_output(json_str: str, model_cls: type[BaseModel]) -> BaseModel | None:
    """Parse LLM JSON output, return None on failure instead of crashing."""
    try:
        return model_cls.model_validate_json(json_str)
    except ValidationError as e:
        print(f"[WARN] LLM output validation failed: {e.error_count()} errors")
        for err in e.errors():
            print(f"  Field: {'.'.join(str(x) for x in err['loc'])}")
            print(f"  Error: {err['msg']}")
        return None
    except json.JSONDecodeError as e:
        print(f"[WARN] LLM returned invalid JSON: {e}")
        return None


# ── 8. model_dump() and JSON schema ──────────────────────────────────────────
print("\n=== Serialization ===")
report_dict = report.model_dump()
report_json = report.model_dump_json(indent=2)
print(f"Dict keys: {list(report_dict.keys())}")
print(f"JSON (first 200 chars):\n{report_json[:200]}...")

# Get JSON schema to pass to LLM as "respond in this format"
schema = ResearchReport.model_json_schema()
print(f"\nJSON Schema title: {schema['title']}")
print(f"Required fields  : {schema.get('required', [])}")

# Exclude certain fields when serializing
compact = report.model_dump(exclude={"generated_at", "model_used"})
print(f"\nCompact dict: {list(compact.keys())}")


# ── 9. Using schema to instruct LLM ──────────────────────────────────────────
def build_structured_output_prompt(schema: dict) -> str:
    """Build a system prompt that tells the LLM what JSON to output."""
    schema_str = json.dumps(schema, indent=2)
    return (
        f"Always respond with valid JSON matching this schema:\n\n"
        f"```json\n{schema_str}\n```\n\n"
        f"Do not include any text outside the JSON object."
    )

prompt = build_structured_output_prompt(ResearchReport.model_json_schema())
print(f"\nStructured output system prompt (first 100 chars):")
print(prompt[:100] + "...")
