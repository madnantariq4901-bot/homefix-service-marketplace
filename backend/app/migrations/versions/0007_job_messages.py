from alembic import op
import sqlalchemy as sa


revision = "0007_job_messages"
down_revision = "0006_custom_service_names"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "job_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_messages_id", "job_messages", ["id"], unique=False)
    op.create_index("ix_job_messages_job_id", "job_messages", ["job_id"], unique=False)
    op.create_index("ix_job_messages_sender_id", "job_messages", ["sender_id"], unique=False)


def downgrade():
    op.drop_index("ix_job_messages_sender_id", table_name="job_messages")
    op.drop_index("ix_job_messages_job_id", table_name="job_messages")
    op.drop_index("ix_job_messages_id", table_name="job_messages")
    op.drop_table("job_messages")