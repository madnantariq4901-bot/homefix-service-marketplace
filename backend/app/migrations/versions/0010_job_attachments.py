from alembic import op
import sqlalchemy as sa


revision = "0010_job_attachments"
down_revision = "0009_targeted_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "job_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_attachments_id", "job_attachments", ["id"], unique=False)
    op.create_index("ix_job_attachments_job_id", "job_attachments", ["job_id"], unique=False)


def downgrade():
    op.drop_index("ix_job_attachments_job_id", table_name="job_attachments")
    op.drop_index("ix_job_attachments_id", table_name="job_attachments")
    op.drop_table("job_attachments")