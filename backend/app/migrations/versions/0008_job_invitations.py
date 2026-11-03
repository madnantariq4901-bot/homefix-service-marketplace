from alembic import op
import sqlalchemy as sa


revision = "0008_job_invitations"
down_revision = "0007_job_messages"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "job_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("invited_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "provider_id", name="uq_job_invitation_provider"),
    )
    op.create_index("ix_job_invitations_id", "job_invitations", ["id"], unique=False)
    op.create_index("ix_job_invitations_job_id", "job_invitations", ["job_id"], unique=False)
    op.create_index("ix_job_invitations_provider_id", "job_invitations", ["provider_id"], unique=False)


def downgrade():
    op.drop_index("ix_job_invitations_provider_id", table_name="job_invitations")
    op.drop_index("ix_job_invitations_job_id", table_name="job_invitations")
    op.drop_index("ix_job_invitations_id", table_name="job_invitations")
    op.drop_table("job_invitations")