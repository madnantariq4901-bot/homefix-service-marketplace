from alembic import op
import sqlalchemy as sa


revision = "0009_targeted_jobs"
down_revision = "0008_job_invitations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("target_provider_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_jobs_target_provider_id_provider_profiles",
        "jobs",
        "provider_profiles",
        ["target_provider_id"],
        ["id"],
    )
    op.create_index("ix_jobs_target_provider_id", "jobs", ["target_provider_id"], unique=False)


def downgrade():
    op.drop_index("ix_jobs_target_provider_id", table_name="jobs")
    op.drop_constraint("fk_jobs_target_provider_id_provider_profiles", "jobs", type_="foreignkey")
    op.drop_column("jobs", "target_provider_id")