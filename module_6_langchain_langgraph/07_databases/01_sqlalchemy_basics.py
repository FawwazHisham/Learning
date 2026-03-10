"""
07_databases/01_sqlalchemy_basics.py
======================================
SQLAlchemy 2.0: Database ORM for AI Agent Systems

CONCEPTS COVERED:
  - Declarative models with mapped_column()
  - Sync and async engines
  - Sessions: add, query, update, delete
  - Relationships (one-to-many, many-to-many)
  - Querying with select()
  - Storing agent conversations, tool calls, memories

WHY SQLALCHEMY FOR AI?
  - Store conversation history permanently
  - Audit trail of agent actions
  - User profiles and preferences
  - Caching expensive LLM responses
"""

import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    String, Integer, Float, Text, Boolean, DateTime, JSON,
    ForeignKey, select, func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)


# ── 1. Base class ─────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── 2. Models — define your database tables as Python classes ─────────────────
class User(Base):
    """Users of the AI agent system."""
    __tablename__ = "users"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True)
    email:      Mapped[str]            = mapped_column(String(255), unique=True, nullable=False)
    name:       Mapped[str]            = mapped_column(String(100), nullable=False)
    api_key:    Mapped[Optional[str]]  = mapped_column(String(100))
    is_active:  Mapped[bool]           = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]       = mapped_column(DateTime, default=datetime.utcnow)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"


class Conversation(Base):
    """A conversation session between a user and the agent."""
    __tablename__ = "conversations"

    id:         Mapped[int]   = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str]   = mapped_column(String(100), unique=True, nullable=False)
    title:      Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at:   Mapped[Optional[datetime]] = mapped_column(DateTime)
    metadata_:  Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)

    # Relationships
    user:     Mapped[User]          = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.created_at")

    def __repr__(self) -> str:
        return f"<Conversation(session_id={self.session_id!r})>"


class Message(Base):
    """Individual messages in a conversation."""
    __tablename__ = "messages"

    id:              Mapped[int]   = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int]   = mapped_column(ForeignKey("conversations.id"), nullable=False)
    role:            Mapped[str]   = mapped_column(String(20), nullable=False)  # human/ai/tool
    content:         Mapped[str]   = mapped_column(Text, nullable=False)
    token_count:     Mapped[Optional[int]] = mapped_column(Integer)
    model_used:      Mapped[Optional[str]] = mapped_column(String(100))
    created_at:      Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tool_calls:      Mapped[Optional[dict]] = mapped_column(JSON)   # for AI messages with tool calls
    tool_call_id:    Mapped[Optional[str]] = mapped_column(String(100))  # for tool messages

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(role={self.role!r}, content={self.content[:30]!r})>"


class AgentMemory(Base):
    """Long-term facts the agent remembers about users."""
    __tablename__ = "agent_memories"

    id:         Mapped[int]   = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=False)
    fact_type:  Mapped[str]   = mapped_column(String(50), nullable=False)  # preference/fact/skill
    fact_key:   Mapped[str]   = mapped_column(String(100), nullable=False)
    fact_value: Mapped[str]   = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LLMCache(Base):
    """Cache expensive LLM responses to avoid redundant API calls."""
    __tablename__ = "llm_cache"

    id:          Mapped[int]   = mapped_column(Integer, primary_key=True)
    prompt_hash: Mapped[str]   = mapped_column(String(64), unique=True, index=True)  # SHA256
    model:       Mapped[str]   = mapped_column(String(100), nullable=False)
    prompt:      Mapped[str]   = mapped_column(Text, nullable=False)
    response:    Mapped[str]   = mapped_column(Text, nullable=False)
    token_count: Mapped[int]   = mapped_column(Integer)
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    hit_count:   Mapped[int]   = mapped_column(Integer, default=0)


# ── 3. Sync engine and session ────────────────────────────────────────────────
SQLITE_URL = "sqlite:///./agent_db.sqlite"
engine = create_engine(SQLITE_URL, echo=False)  # echo=True logs all SQL

# Create all tables
Base.metadata.create_all(engine)
print("=== SQLAlchemy 2.0 Basics ===")
print(f"Database: {SQLITE_URL}")
print(f"Tables created: {list(Base.metadata.tables.keys())}")


# ── 4. CRUD operations ────────────────────────────────────────────────────────
def create_user(email: str, name: str) -> User:
    """Create and persist a new user."""
    with Session(engine) as session:
        user = User(email=email, name=name, preferences={"theme": "dark"})
        session.add(user)
        session.commit()
        session.refresh(user)  # load the generated id
        print(f"Created user: {user}")
        return user


def get_user_by_email(email: str) -> Optional[User]:
    """Query a user by email."""
    with Session(engine) as session:
        stmt = select(User).where(User.email == email)
        return session.scalar(stmt)  # returns None if not found


def create_conversation(user_id: int, session_id: str) -> Conversation:
    """Create a new conversation for a user."""
    with Session(engine) as session:
        conv = Conversation(user_id=user_id, session_id=session_id)
        session.add(conv)
        session.commit()
        session.refresh(conv)
        return conv


def add_message(conversation_id: int, role: str, content: str, model: str = None) -> Message:
    """Add a message to a conversation."""
    with Session(engine) as session:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_used=model,
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg


def get_conversation_messages(session_id: str) -> list[Message]:
    """Get all messages for a conversation."""
    with Session(engine) as session:
        stmt = (
            select(Message)
            .join(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Message.created_at)
        )
        return list(session.scalars(stmt))


def get_user_stats(user_id: int) -> dict:
    """Aggregate query: get user's conversation stats."""
    with Session(engine) as session:
        stmt = (
            select(
                func.count(Conversation.id).label("total_conversations"),
                func.count(Message.id).label("total_messages"),
            )
            .join(Message, isouter=True)
            .where(Conversation.user_id == user_id)
        )
        row = session.execute(stmt).one()
        return {
            "total_conversations": row.total_conversations,
            "total_messages":      row.total_messages,
        }


# ── 5. Demo: Full CRUD workflow ───────────────────────────────────────────────
print("\n=== CRUD Demo ===")

# Create user
user = create_user("alice@example.com", "Alice")
print(f"User ID: {user.id}")

# Create conversation
conv = create_conversation(user.id, "sess_001")
print(f"Conversation ID: {conv.id}")

# Add messages
msg1 = add_message(conv.id, "human", "What is LangGraph?")
msg2 = add_message(conv.id, "ai", "LangGraph is a framework for building stateful AI agents.", model="gpt-4o-mini")
msg3 = add_message(conv.id, "human", "Can you give me an example?")

# Query
messages = get_conversation_messages("sess_001")
print(f"\nMessages in conversation:")
for msg in messages:
    print(f"  [{msg.role}]: {msg.content[:50]}")

stats = get_user_stats(user.id)
print(f"\nUser stats: {stats}")


# ── 6. Async SQLAlchemy ───────────────────────────────────────────────────────
ASYNC_SQLITE_URL = "sqlite+aiosqlite:///./agent_db_async.sqlite"

async_engine = create_async_engine(ASYNC_SQLITE_URL, echo=False)
AsyncSessionFactory = async_sessionmaker(async_engine, expire_on_commit=False)


async def async_crud_demo():
    """Async CRUD operations — essential for async agent code."""
    print("\n=== Async SQLAlchemy ===")

    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert
    async with AsyncSessionFactory() as session:
        async with session.begin():
            user = User(email="bob@example.com", name="Bob")
            session.add(user)

        await session.refresh(user)
        print(f"Async user created: {user}")

    # Query
    async with AsyncSessionFactory() as session:
        stmt = select(User).where(User.name == "Bob")
        result = await session.execute(stmt)
        bob = result.scalar_one_or_none()
        print(f"Async query: {bob}")

    # Cleanup
    await async_engine.dispose()


asyncio.run(async_crud_demo())


# ── 7. Repository pattern for AI agents ──────────────────────────────────────
class ConversationRepository:
    """
    Repository pattern: encapsulate all DB logic for conversations.
    This keeps your agent code free of raw SQL.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, session_id: str) -> Conversation:
        conv = Conversation(user_id=user_id, session_id=session_id)
        self.session.add(conv)
        self.session.flush()  # get the id without committing
        return conv

    def get_by_session_id(self, session_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        return self.session.scalar(stmt)

    def get_recent_for_user(self, user_id: int, limit: int = 10) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def add_message(self, conv_id: int, role: str, content: str) -> Message:
        msg = Message(conversation_id=conv_id, role=role, content=content)
        self.session.add(msg)
        self.session.flush()
        return msg


# Usage of repository pattern:
with Session(engine) as session:
    repo = ConversationRepository(session)
    recent = repo.get_recent_for_user(user_id=1, limit=5)
    print(f"\nRepository: found {len(recent)} recent conversations")
    session.commit()

print("\n✓ SQLAlchemy key patterns:")
print("  mapped_column()          → type-safe column definitions")
print("  Mapped[Type]             → type hints that match DB types")
print("  with Session(engine)     → sync context manager")
print("  async with AsyncSession  → async context manager")
print("  select(Model).where(...) → modern 2.0 query syntax")
