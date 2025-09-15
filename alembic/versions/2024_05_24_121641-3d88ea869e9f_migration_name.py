"""migration-name
Revision ID: 3d88ea869e9f
Revises: 0508925c121a
Create Date: 2024-05-24 12:16:41.891695+05:30
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3d88ea869e9f"
down_revision: Union[str, None] = "0508925c121a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


existing_type = sa.Enum(
    "CORE",
    "ISEARCHUI",
    "JOB",
    name="serviceenum",
)
new_type = sa.Enum(
    "CORE",
    "ISEARCHUI",
    "JOB",
    "EXTRAS",
    name="serviceenum",
)


def upgrade():
    op.alter_column(
        "core_audit_logs",
        "service",
        existing_type=existing_type,
        type_=new_type,
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "core_audit_logs",
        "service",
        existing_type=new_type,
        type_=existing_type,
        existing_nullable=False,
    )
