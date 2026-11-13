"""Add the required course level to a populated catalog."""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("level", sa.Text(), nullable=True))
    op.execute("""
        UPDATE courses
        SET level = CASE WHEN is_elective THEN 'beginner' ELSE 'intermediate' END
    """)
    op.alter_column("courses", "level", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    op.drop_column("courses", "level")
