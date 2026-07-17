"""Compatibility migrations for the local SQLite database."""

from __future__ import annotations

from sqlalchemy import Engine, inspect, text


SQLITE_OPPORTUNITY_COLUMNS = {
    "link_verification_status": "VARCHAR(30) NOT NULL DEFAULT 'not_checked'",
    "last_verified_at": "DATETIME",
}


def migrate_sqlite_schema(engine: Engine) -> None:
    """Idempotently add missing opportunity columns to an existing SQLite database."""

    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "phd_opportunities" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("phd_opportunities")
    }
    missing_columns = {
        name: definition
        for name, definition in SQLITE_OPPORTUNITY_COLUMNS.items()
        if name not in existing_columns
    }

    with engine.begin() as connection:
        for name, definition in missing_columns.items():
            connection.execute(
                text(f"ALTER TABLE phd_opportunities ADD COLUMN {name} {definition}")
            )
