from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_custom_service_names"
down_revision = "0005_add_missing_category_enum_values"
branch_labels = None
depends_on = None

CATEGORY_NAMES = (
    "PLUMBER",
    "ELECTRICIAN",
    "CARPENTER",
    "MECHANIC",
    "AC_TECHNICIAN",
    "PAINTER",
    "CLEANER",
    "MASON",
)


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        category_enum = postgresql.ENUM(name="categoryname", create_type=False)
        op.alter_column(
            "service_categories",
            "name",
            existing_type=category_enum,
            type_=sa.String(length=80),
            existing_nullable=False,
            postgresql_using="lower(name::text)",
        )
        category_enum.drop(bind, checkfirst=True)
    else:
        with op.batch_alter_table("service_categories") as batch_op:
            batch_op.alter_column(
                "name",
                existing_type=sa.String(length=13),
                type_=sa.String(length=80),
                existing_nullable=False,
            )
        op.execute("UPDATE service_categories SET name = lower(name)")


def downgrade():
    bind = op.get_bind()
    allowed_names = tuple(name.lower() for name in CATEGORY_NAMES)
    names = {name.lower() for (name,) in bind.execute(sa.text("SELECT DISTINCT name FROM service_categories"))}
    if not names.issubset(allowed_names):
        raise RuntimeError("Cannot downgrade while custom service names exist")

    if bind.dialect.name == "postgresql":
        category_enum = postgresql.ENUM(*CATEGORY_NAMES, name="categoryname", create_type=False)
        category_enum.create(bind, checkfirst=True)
        op.alter_column(
            "service_categories",
            "name",
            existing_type=sa.String(length=80),
            type_=category_enum,
            existing_nullable=False,
            postgresql_using="upper(name)::categoryname",
        )
    else:
        with op.batch_alter_table("service_categories") as batch_op:
            batch_op.alter_column(
                "name",
                existing_type=sa.String(length=80),
                type_=sa.String(length=13),
                existing_nullable=False,
            )
        op.execute("UPDATE service_categories SET name = upper(name)")