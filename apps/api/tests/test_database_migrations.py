from sqlalchemy import create_engine, inspect, text

from app.migrations import migrate_sqlite_schema


def test_adds_link_verification_fields_to_an_existing_sqlite_database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE phd_opportunities (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL
                )
                """
            )
        )
        connection.execute(
            text("INSERT INTO phd_opportunities (title) VALUES ('Existing record')")
        )

    migrate_sqlite_schema(engine)
    migrate_sqlite_schema(engine)

    columns = {
        column["name"] for column in inspect(engine).get_columns("phd_opportunities")
    }
    assert "link_verification_status" in columns
    assert "last_verified_at" in columns

    with engine.connect() as connection:
        status = connection.scalar(
            text("SELECT link_verification_status FROM phd_opportunities")
        )
    assert status == "not_checked"
