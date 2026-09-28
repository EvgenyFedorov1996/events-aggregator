"""add provider ticket id

Revision ID: 26f766edbc3a
Revises: f4f8de02c9fa
Create Date: 2026-09-28 22:05:59.478264

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "26f766edbc3a"
down_revision: Union[str, Sequence[str], None] = "f4f8de02c9fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tickets",
        sa.Column(
            "provider_ticket_id",
            sa.UUID(),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_tickets_provider_ticket_id",
        "tickets",
        ["provider_ticket_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_tickets_provider_ticket_id",
        "tickets",
        type_="unique",
    )
    op.drop_column(
        "tickets",
        "provider_ticket_id",
    )