from alembic import op # pyright: ignore[reportMissingImports]
import sqlalchemy as sa # pyright: ignore[reportMissingImports]
from sqlalchemy.dialects import postgresql  # pyright: ignore[reportMissingImports]

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("CUSTOMER", "PROVIDER", "ADMIN", name="userrole", create_type=False)
category_name = postgresql.ENUM("PLUMBER", "ELECTRICIAN", "CARPENTER", "MECHANIC", name="categoryname", create_type=False)
job_status = postgresql.ENUM("REQUESTED", "QUOTED", "ACCEPTED", "EN_ROUTE", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="jobstatus", create_type=False)


def upgrade():
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    category_name.create(bind, checkfirst=True)
    job_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "service_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", category_name, nullable=False),
        sa.Column("base_hourly_rate", sa.Float(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_service_categories_id", "service_categories", ["id"], unique=False)

    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("current_lat", sa.Float(), nullable=True),
        sa.Column("current_lng", sa.Float(), nullable=True),
        sa.Column("rating_avg", sa.Float(), nullable=False),
        sa.Column("rating_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_provider_profiles_id", "provider_profiles", ["id"], unique=False)

    op.create_table(
        "provider_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["service_categories.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_id", "category_id", name="uq_provider_category"),
    )
    op.create_index("ix_provider_skills_id", "provider_skills", ["id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("status", job_status, nullable=False),
        sa.Column("quoted_amount", sa.Float(), nullable=True),
        sa.Column("final_amount", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["service_categories.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"], unique=False)

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("quoted_amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "provider_id", name="uq_quote_job_provider"),
    )
    op.create_index("ix_quotes_id", "quotes", ["id"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["provider_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_review_per_job"),
    )
    op.create_index("ix_reviews_id", "reviews", ["id"], unique=False)


def downgrade():
    op.drop_index("ix_reviews_id", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_quotes_id", table_name="quotes")
    op.drop_table("quotes")
    op.drop_index("ix_jobs_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_provider_skills_id", table_name="provider_skills")
    op.drop_table("provider_skills")
    op.drop_index("ix_provider_profiles_id", table_name="provider_profiles")
    op.drop_table("provider_profiles")
    op.drop_index("ix_service_categories_id", table_name="service_categories")
    op.drop_table("service_categories")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
    job_status.drop(op.get_bind(), checkfirst=True)
    category_name.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
