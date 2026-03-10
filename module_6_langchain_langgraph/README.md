# Module 6: AI Agents, LangChain & LangGraph — Complete Tutorial

A comprehensive, hands-on guide to building production-grade AI agent systems
from scratch to advanced patterns.

---

## What You Will Learn

| Topic | Libraries Covered |
|-------|------------------|
| Environment & Observability | `python-dotenv`, `loguru`, `rich` |
| Resilient HTTP Clients | `aiohttp`, `httpx`, `tenacity` |
| Data Validation | `pydantic` v2 |
| LangChain Fundamentals | `langchain`, `openai`, `anthropic` |
| State Machine Agents | `langgraph` |
| Persistent Storage | `sqlalchemy`, `alembic` |
| Caching & Sessions | `redis` |
| Testing AI Systems | `pytest`, `pytest-asyncio` |

---

## Course Structure

```
module_6_langchain_langgraph/
├── 01_foundations/          ← Setup, logging, rich output, retry logic
├── 02_langchain_basics/     ← Prompts, chains, models, memory
├── 03_pydantic_models/      ← Structured outputs, validation
├── 04_async_programming/    ← aiohttp, httpx, async patterns
├── 05_langgraph_basics/     ← Graphs, nodes, edges, state
├── 06_langgraph_advanced/   ← Multi-agent, branching, loops
├── 07_databases/            ← SQLAlchemy ORM + Alembic migrations
├── 08_redis_caching/        ← Caching, sessions, pub/sub
├── 09_ai_agents/            ← Full agent architectures
├── 10_testing/              ← pytest + pytest-asyncio for AI
└── 11_capstone_project/     ← Full production agent system
```

---

## Prerequisites

```bash
pip install anthropic>=0.25.0 openai>=1.0.0 pydantic>=2.0.0 \
            python-dotenv>=1.0.0 rich>=13.0.0 loguru>=0.7.0 \
            tenacity>=8.0.0 aiohttp>=3.9.0 sqlalchemy>=2.0.0 \
            alembic>=1.13.0 redis>=5.0.0 pytest>=8.0.0 \
            pytest-asyncio>=0.23.0 httpx>=0.27.0 \
            langgraph>=0.1.0 langchain>=0.2.0 \
            langchain-openai langchain-anthropic
```

Copy `.env.example` → `.env` and fill in your API keys.

---

## Key Concepts at a Glance

### What is an AI Agent?

An **AI Agent** is a system that:
1. **Perceives** its environment (tools, data, user input)
2. **Reasons** about what action to take (LLM planning)
3. **Acts** by calling tools or APIs
4. **Observes** results and loops until done

```
User → Agent → [Think → Act → Observe] → User
                    ↑___________↓
                     (loop until done)
```

### LangChain vs LangGraph

| | LangChain | LangGraph |
|-|-----------|-----------|
| **Model** | Linear chains | State machine graphs |
| **Best for** | Simple pipelines | Complex, branching agents |
| **Control flow** | Sequential | Any DAG or cyclic graph |
| **State** | Basic memory | Full typed state management |
