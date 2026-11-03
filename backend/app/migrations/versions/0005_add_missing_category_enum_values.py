from alembic import op
import sqlalchemy as sa

revision = "0005_add_missing_category_enum_values"
down_revision = ("0004_password_reset_tokens", "0004_review_experience")
branch_labels = None
depends_on = None

NEW_CATEGORIES = ["AC_TECHNICIAN", "PAINTER", "CLEANER", "MASON"]


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            for val in NEW_CATEGORIES:
                op.execute(sa.text(f"ALTER TYPE categoryname ADD VALUE IF NOT EXISTS '{val}'"))


def downgrade():
    pass
