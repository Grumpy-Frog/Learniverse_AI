"""allow refusal tutor message type

Revision ID: b658aab2f51f
Revises: e3f5a1a8c1a8
Create Date: 2026-05-30 06:08:06.725758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b658aab2f51f'
down_revision: Union[str, Sequence[str], None] = 'e3f5a1a8c1a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_tutor_message_type",
        "tutor_messages",
        type_="check",
    )

    op.create_check_constraint(
        "ck_tutor_message_type",
        "tutor_messages",
        "message_type IN ('story', 'chat', 'refusal')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_tutor_message_type",
        "tutor_messages",
        type_="check",
    )

    op.create_check_constraint(
        "ck_tutor_message_type",
        "tutor_messages",
        "message_type IN ('story', 'chat')",
    )