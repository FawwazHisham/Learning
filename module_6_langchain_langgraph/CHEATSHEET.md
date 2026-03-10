# AI Agents, LangChain & LangGraph — Master Cheatsheet

---

## python-dotenv

```python
from dotenv import load_dotenv
import os

load_dotenv()                          # load .env file
val = os.getenv("KEY", "default")      # read with default
os.environ["KEY"]                      # read — raises KeyError if missing
```

---

## loguru

```python
from loguru import logger

logger.remove()                        # remove default handler
logger.add(sys.stdout, level="DEBUG")  # add console sink
logger.add("app.log", rotation="10 MB", retention="7 days", serialize=True)

logger.debug("msg")
logger.info("msg")
logger.success("msg")                  # loguru-specific
logger.warning("msg")
logger.error("msg")

child = logger.bind(user_id="u1")      # structured context
child.info("User action")              # → includes user_id in every log

@logger.catch(reraise=True)            # auto-log exceptions
def risky(): ...
```

---

## rich

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn

console = Console()
console.print("[bold green]Hello![/bold green]")
console.print(Panel("Content", title="Title", border_style="cyan"))

table = Table("Col1", "Col2")
table.add_row("val1", "val2")
console.print(table)

with Progress(SpinnerColumn(), ...) as p:
    task = p.add_task("Working...", total=100)
    p.advance(task, 10)
```

---

## tenacity

```python
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(6),
    wait=wait_random_exponential(min=1, max=60),  # exponential + jitter
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
async def call_llm(prompt): ...

# Combine stop conditions
stop=(stop_after_attempt(10) | stop_after_delay(60))
```

---

## Pydantic v2

```python
from pydantic import BaseModel, Field, field_validator, model_validator

class MyModel(BaseModel):
    name:  str        = Field(min_length=1, max_length=100)
    score: float      = Field(ge=0.0, le=1.0)
    tags:  list[str]  = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v): return v.title()

    @model_validator(mode="after")
    def check_cross_fields(self): ...

obj = MyModel(name="alice", score=0.9)
obj.model_dump()                       # → dict
obj.model_dump_json()                  # → JSON string
MyModel.model_validate_json(json_str)  # parse from JSON
MyModel.model_json_schema()            # → JSON Schema dict
```

---

## LangChain — Models & Messages

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

response = model.invoke([SystemMessage("You are..."), HumanMessage("Hi")])
response.content                       # → str

for chunk in model.stream(messages):   # streaming
    print(chunk.content, end="")

responses = model.batch([msgs1, msgs2, msgs3])  # parallel

# Structured output
structured = model.with_structured_output(MyPydanticModel)
result: MyPydanticModel = structured.invoke(messages)
```

---

## LangChain — LCEL Chains

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}."),
    ("human",  "{question}"),
])

chain = prompt | model | StrOutputParser()
chain.invoke({"role": "expert", "question": "What is AI?"})
chain.stream(inputs)
chain.batch([inputs1, inputs2])

# Parallel branches (same input → multiple outputs)
parallel = RunnableParallel(
    summary=(summary_prompt | model | StrOutputParser()),
    keywords=(keyword_prompt | model | StrOutputParser()),
)

# Pass-through original input
chain = RunnableParallel(
    original=RunnablePassthrough(),
    processed=some_chain,
)
```

---

## LangChain — Tools

```python
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the web. Args: query: what to search for."""
    return f"results for {query}"

model_with_tools = model.bind_tools([search])
response = model_with_tools.invoke(messages)
response.tool_calls  # → [{"name": "search", "args": {...}, "id": "..."}]

# Execute tools
from langgraph.prebuilt import ToolNode
tool_node = ToolNode([search])
result = tool_node.invoke(state)  # returns ToolMessage objects
```

---

## LangGraph — Core Concepts

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]  # APPEND semantics
    counter:  int                             # REPLACE semantics

def my_node(state: State) -> dict:           # returns PARTIAL state
    return {"counter": state["counter"] + 1}

graph = StateGraph(State)
graph.add_node("node_a", my_node)
graph.add_edge(START, "node_a")
graph.add_edge("node_a", END)

# Conditional routing
def router(state: State) -> str:             # returns node NAME
    return "node_b" if state["counter"] > 5 else "node_a"

graph.add_conditional_edges("node_a", router, {"node_a": "node_a", "node_b": "node_b"})

compiled = graph.compile()
result = compiled.invoke({"messages": [], "counter": 0})
```

---

## LangGraph — ReAct Agent

```python
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# The complete ReAct pattern:
graph = StateGraph(AgentState)
graph.add_node("agent", agent_fn)          # LLM reasoning
graph.add_node("tools", ToolNode(tools))   # tool execution

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition)  # tools or END?
graph.add_edge("tools", "agent")           # always back to agent

memory = MemorySaver()
agent = graph.compile(checkpointer=memory)

# Run
result = agent.invoke({"messages": [HumanMessage("...")]},
                      config={"configurable": {"thread_id": "sess_001"}})

# Stream
for event in agent.stream(state, stream_mode="values"):
    last = event["messages"][-1]

# Memory: same thread_id = same conversation
agent.get_state(config)                    # current state
list(agent.get_state_history(config))      # all checkpoints
```

---

## LangGraph — Multi-Agent Supervisor

```python
# Supervisor pattern
graph.add_node("supervisor",  supervisor_fn)
graph.add_node("researcher",  researcher_fn)
graph.add_node("writer",      writer_fn)

graph.add_edge(START, "supervisor")

def route(state) -> str:
    return state["next_agent"]  # or END

graph.add_conditional_edges("supervisor", route,
    {"researcher": "researcher", "writer": "writer", END: END})

graph.add_edge("researcher", "supervisor")  # return to supervisor
graph.add_edge("writer",     "supervisor")
```

---

## SQLAlchemy 2.0

```python
from sqlalchemy import create_engine, String, Integer, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id:    Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)

engine = create_engine("sqlite:///./app.db")
Base.metadata.create_all(engine)

with Session(engine) as session:
    user = User(email="alice@example.com")
    session.add(user)
    session.commit()

    result = session.scalar(select(User).where(User.email == "alice@example.com"))

# Async
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
engine = create_async_engine("sqlite+aiosqlite:///./app.db")
AsyncSession = async_sessionmaker(engine)

async with AsyncSession() as session:
    result = await session.execute(select(User))
```

---

## Alembic

```bash
alembic init alembic                         # initialize
alembic revision --autogenerate -m "desc"    # create migration
alembic upgrade head                         # apply migrations
alembic downgrade -1                         # rollback one
alembic current                              # show current version
alembic history                              # show all migrations
```

```python
# env.py — critical config
from your_models import Base
target_metadata = Base.metadata  # enables --autogenerate
```

---

## Redis

```python
import redis
r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

# Strings
r.setex("key", 3600, "value")              # set with TTL (seconds)
r.get("key")                               # → "value" or None
r.delete("key")

# Hashes (for sessions)
r.hset("session:001", mapping={"user": "alice", "turn": "1"})
r.hgetall("session:001")                   # → dict
r.hincrby("session:001", "turn", 1)        # atomic increment

# Rate limiting
r.zadd("ratelimit:user1", {str(time.time()): time.time()})
r.zcount("ratelimit:user1", time.time() - 60, time.time())

# Async Redis
import redis.asyncio as aioredis
client = aioredis.Redis.from_url("redis://localhost:6379")
await client.setex("key", 60, "value")
await client.get("key")
```

---

## aiohttp & httpx

```python
import asyncio, aiohttp, httpx

# aiohttp — async HTTP
async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
        data = await resp.json()

# httpx — sync + async
with httpx.Client() as client:             # sync
    r = client.get(url)

async with httpx.AsyncClient() as client:  # async
    r = await client.get(url)

# Concurrent requests
results = await asyncio.gather(*[fetch(url) for url in urls])

# Rate limiting
sem = asyncio.Semaphore(5)                 # max 5 concurrent
async with sem:
    result = await api_call()
```

---

## pytest + pytest-asyncio

```python
# pytest basics
def test_something():
    assert calculator("2+2") == 4

class TestGroup:
    def test_a(self): ...
    def test_b(self): ...

@pytest.mark.parametrize("input,expected", [("2+2", 4), ("5*5", 25)])
def test_param(input, expected): assert eval(input) == expected

# Async tests
@pytest.mark.asyncio
async def test_async():
    result = await async_function()
    assert result is not None

# Fixtures
@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="Response")
    return mock

def test_with_fixture(mock_llm):
    result = my_agent(mock_llm)
    mock_llm.invoke.assert_called_once()

# Mocking
with patch("module.ClassName") as MockClass:
    MockClass.return_value.method.return_value = "mocked"
    result = function_under_test()

# conftest.py — auto fixtures
@pytest.fixture(autouse=True)
def no_api_calls(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
```

---

## Key Patterns Summary

```
1. Agent loop:       START → agent ⟺ tools → END
2. Multi-agent:      START → supervisor ⟺ {researcher, writer, ...} → END
3. State:            TypedDict with Annotated[list, add_messages] for messages
4. Memory:           MemorySaver (dev) / SqliteSaver (prod) + thread_id
5. Tools:            @tool decorator → bind_tools() → ToolNode → ToolMessage
6. Structured output: model.with_structured_output(PydanticModel)
7. Caching:          Redis setex(hash(prompt), TTL, response)
8. Persistence:      SQLAlchemy models → Alembic migrations
9. Retry:            @retry(stop_after_attempt(6), wait_random_exponential(1,60))
10. Testing:         Mock LLM, test nodes in isolation, conftest.py safety fixture
```
