"""Read each mapped table and check its constraint and index names against PostgreSQL."""

from sqlalchemy import select, text

from db import Base, SessionLocal
from models import Course, Enrollment, Student


DB_NAMES = """
SELECT conname FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'u', 'f', 'c')
UNION
SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
"""


def main() -> int:
    with SessionLocal() as db:
        for model in (Course, Student, Enrollment):
            rows = db.scalars(select(model)).all()
            print(f"{model.__tablename__}: {len(rows)} rows")
        stored = {name for name in db.scalars(text(DB_NAMES)) if not name.startswith("alembic")}

    declared = {
        str(item.name)
        for table in Base.metadata.tables.values()
        for item in (*table.constraints, *table.indexes)
    }
    print("names only in models:", sorted(declared - stored) or "none")
    print("names only in database:", sorted(stored - declared) or "none")
    return int(declared != stored)


if __name__ == "__main__":
    raise SystemExit(main())
