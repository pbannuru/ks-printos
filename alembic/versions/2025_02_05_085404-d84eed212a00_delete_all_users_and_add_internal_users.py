"""delete-all-users-and-add-internal-users

Revision ID: d84eed212a00
Revises: 26ede02b7b89
Create Date: 2025-02-05 08:54:04.025599+05:30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d84eed212a00"
down_revision: Union[str, None] = "26ede02b7b89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM isearchui_users")

    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('aloysius-raja.p@hp.com','Admin', 'auto-migration@hp.com')"""
    )
    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('joharapuram.reddy@hp.com','Admin', 'auto-migration@hp.com')"""
    )
    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('kathiravan.k@hp.com','Admin', 'auto-migration@hp.com')"""
    )
    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('prakash.pattanaik@hp.com','Admin', 'auto-migration@hp.com')"""
    )
    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('neha.prasad@hp.com','Admin', 'auto-migration@hp.com')"""
    )
    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('b-pavan.kumar@hp.com','Admin', 'auto-migration@hp.com')"""
    )
    op.execute(
        """INSERT INTO isearchui_users (email,`role`, created_by) VALUES ('anantha.krishna.ramachandra@hp.com','Admin', 'auto-migration@hp.com')"""
    )


def downgrade() -> None:
    op.execute("DELETE FROM isearchui_users")
