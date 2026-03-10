"""
07_databases/02_alembic_migrations.py
======================================
Alembic: Database Migrations for Production AI Systems

CONCEPTS COVERED:
  - What migrations are and why you need them
  - Setting up Alembic in a project
  - Auto-generating migrations from SQLAlchemy models
  - Running migrations
  - Rollback (downgrade)
  - Data migrations (not just schema)
  - Environment setup

WHY MIGRATIONS MATTER FOR AI SYSTEMS:
  Your agent evolves. You'll add new fields:
    - Agent conversation summaries
    - Token usage tracking
    - New memory fields
  Alembic lets you evolve the schema safely, without losing data.

NOTE: This file explains Alembic setup and commands.
      Alembic is configured via alembic.ini and env.py files.
"""


# ── 1. Project setup commands ─────────────────────────────────────────────────
SETUP_COMMANDS = """
# 1. Install
pip install alembic sqlalchemy

# 2. Initialize Alembic in your project
cd /path/to/project
alembic init alembic

# This creates:
#   alembic/
#     env.py          ← configure your DB URL and models
#     script.py.mako  ← migration file template
#     versions/       ← individual migration files
#   alembic.ini       ← main config file
"""


# ── 2. alembic.ini configuration ─────────────────────────────────────────────
ALEMBIC_INI = """
# alembic.ini
[alembic]
# Path to migration scripts
script_location = alembic

# Database URL (override with environment variable in env.py)
sqlalchemy.url = sqlite:///./agent_db.sqlite
"""


# ── 3. env.py — critical file! ─────────────────────────────────────────────────
ENV_PY = '''
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import load_dotenv

# Import ALL your models so Alembic can detect them
from your_app.models import Base  # ← import your SQLAlchemy Base

load_dotenv()

config = context.config

# Override DB URL from environment variable
db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# CRITICAL: tell Alembic about your models
target_metadata = Base.metadata  # ← this enables --autogenerate


def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


# ── 4. CLI commands reference ─────────────────────────────────────────────────
CLI_COMMANDS = """
# ─── Generate & Apply Migrations ────────────────────────────────────────────

# Auto-generate a migration from your model changes
alembic revision --autogenerate -m "add token_count to messages"
# Creates: alembic/versions/abc123_add_token_count_to_messages.py

# Apply all pending migrations
alembic upgrade head

# Apply one migration at a time
alembic upgrade +1

# ─── Rollback ────────────────────────────────────────────────────────────────

# Rollback last migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade abc123

# Rollback everything
alembic downgrade base

# ─── Inspection ──────────────────────────────────────────────────────────────

# See current database version
alembic current

# See migration history
alembic history --verbose

# Show pending migrations
alembic heads

# Show migration as SQL (without executing)
alembic upgrade head --sql
"""


# ── 5. Example migration file ─────────────────────────────────────────────────
MIGRATION_EXAMPLE = '''
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001abc
Revises:
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "001abc"
down_revision = None  # None = this is the first migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    op.create_table(
        "users",
        sa.Column("id",         sa.Integer(),    nullable=False),
        sa.Column("email",      sa.String(255),  nullable=False),
        sa.Column("name",       sa.String(100),  nullable=False),
        sa.Column("created_at", sa.DateTime(),   nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "conversations",
        sa.Column("id",         sa.Integer(),    nullable=False),
        sa.Column("user_id",    sa.Integer(),    nullable=False),
        sa.Column("session_id", sa.String(100),  nullable=False),
        sa.Column("created_at", sa.DateTime(),   nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )


def downgrade() -> None:
    """Drop tables in reverse order."""
    op.drop_table("conversations")
    op.drop_table("users")
'''


# ── 6. Adding a column (common migration) ────────────────────────────────────
ADD_COLUMN_MIGRATION = '''
# alembic/versions/002_add_token_usage.py
"""Add token usage tracking to messages

Revision ID: 002def
Revises: 001abc
"""
from alembic import op
import sqlalchemy as sa

revision = "002def"
down_revision = "001abc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to existing table
    with op.batch_alter_table("messages") as batch_op:
        batch_op.add_column(sa.Column("prompt_tokens",  sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("completion_tokens", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("total_cost_usd", sa.Float(), nullable=True))

    # Add index for efficient cost reporting
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_created_at", table_name="messages")
    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_column("total_cost_usd")
        batch_op.drop_column("completion_tokens")
        batch_op.drop_column("prompt_tokens")
'''


# ── 7. Data migration (not just schema) ───────────────────────────────────────
DATA_MIGRATION = '''
# alembic/versions/003_backfill_user_names.py
"""Backfill user names from email

Revision ID: 003ghi
Revises: 002def
"""
from alembic import op
import sqlalchemy as sa

revision = "003ghi"
down_revision = "002def"

def upgrade() -> None:
    # Get connection to run raw SQL data migrations
    conn = op.get_bind()

    # Update all users with empty names to use email prefix
    result = conn.execute(sa.text("SELECT id, email FROM users WHERE name = \'\'"))
    for row in result:
        name = row.email.split("@")[0].title()
        conn.execute(
            sa.text("UPDATE users SET name = :name WHERE id = :id"),
            {"name": name, "id": row.id}
        )

def downgrade() -> None:
    pass  # Data migrations rarely need downgrade
'''


# ── 8. Programmatic migration running ─────────────────────────────────────────
PROGRAMMATIC_USAGE = '''
# Run migrations programmatically (e.g., in app startup)
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run pending migrations on startup."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Database migrations complete")

# Call this in your app startup:
# run_migrations()
'''


# ── Demo: Show all content ────────────────────────────────────────────────────
if __name__ == "__main__":
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.panel import Panel

    console = Console()

    console.print(Panel("[bold]Alembic Migration Guide[/bold]", border_style="cyan"))

    console.print("\n[bold cyan]1. Setup Commands[/bold cyan]")
    console.print(Syntax(SETUP_COMMANDS.strip(), "bash", theme="monokai"))

    console.print("\n[bold cyan]2. CLI Commands Reference[/bold cyan]")
    console.print(Syntax(CLI_COMMANDS.strip(), "bash", theme="monokai"))

    console.print("\n[bold cyan]3. Example Migration File[/bold cyan]")
    console.print(Syntax(MIGRATION_EXAMPLE.strip(), "python", theme="monokai"))

    console.print("\n[bold green]✓ Alembic workflow:[/bold green]")
    console.print("  1. Change your SQLAlchemy model")
    console.print("  2. alembic revision --autogenerate -m 'describe change'")
    console.print("  3. Review the generated migration file")
    console.print("  4. alembic upgrade head")
    console.print("  5. Deploy!")
