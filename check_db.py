from sqlalchemy import text

from db import engine


if __name__ == "__main__":
    with engine.connect() as connection:
        database, user, version = connection.execute(text(
            "SELECT current_database(), current_user, current_setting('server_version')"
        )).one()
    print(f"connected to {database} as {user}, PostgreSQL {version}")
