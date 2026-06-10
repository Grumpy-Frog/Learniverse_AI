"""add custom tutor ai chat

Revision ID: 50776829058a
Revises: 91fa4def997e
Create Date: 2026-06-10 23:25:28.107403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50776829058a'
down_revision: Union[str, Sequence[str], None] = '91fa4def997e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_study_artifact_type",
        "study_artifacts",
        type_="check",
    )

    op.create_check_constraint(
        "ck_study_artifact_type",
        "study_artifacts",
        "artifact_type IN ("
        "'mind_map', "
        "'worksheet', "
        "'formula_sheet', "
        "'important_questions', "
        "'key_points', "
        "'glossary', "
        "'revision_checklist', "
        "'study_plan', "
        "'mnemonic_set'"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_study_artifact_type",
        "study_artifacts",
        type_="check",
    )

    op.create_check_constraint(
        "ck_study_artifact_type",
        "study_artifacts",
        "artifact_type IN ("
        "'mind_map', "
        "'worksheet', "
        "'formula_sheet', "
        "'important_questions'"
        ")",
    )
