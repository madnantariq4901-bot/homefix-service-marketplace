from alembic import op # pyright: ignore[reportMissingImports]
import sqlalchemy as sa # pyright: ignore[reportMissingImports]

revision = "0002_provider_identity_documents"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("provider_profiles", sa.Column("identity_front_path", sa.String(), nullable=True))
    op.add_column("provider_profiles", sa.Column("identity_back_path", sa.String(), nullable=True))
    op.add_column("provider_profiles", sa.Column("identity_selfie_path", sa.String(), nullable=True))
    op.execute(
        """
        UPDATE provider_profiles
        SET is_verified = TRUE
        WHERE (
            SELECT COUNT(*)
            FROM jobs
            WHERE jobs.provider_id = provider_profiles.id
              AND jobs.status = 'COMPLETED'
        ) >= 5
        """
    )


def downgrade():
    op.drop_column("provider_profiles", "identity_selfie_path")
    op.drop_column("provider_profiles", "identity_back_path")
    op.drop_column("provider_profiles", "identity_front_path")
