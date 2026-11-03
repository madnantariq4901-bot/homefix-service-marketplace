from alembic import op  # pyright: ignore[reportMissingImports]
import sqlalchemy as sa  # pyright: ignore[reportMissingImports]

revision = "0004_review_experience"
down_revision = "0003_customer_completion_and_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "reviews",
        sa.Column("experience", sa.String(length=20), server_default="Good", nullable=False),
    )


def downgrade():
    op.drop_column("reviews", "experience")
