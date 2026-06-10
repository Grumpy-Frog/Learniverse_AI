"""add mini study tool artifact types

Revision ID: 0a24d6c5ae3f
Revises: cad8dee59dfe
Create Date: 2026-06-10 23:00:41.700782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a24d6c5ae3f'
down_revision: Union[str, Sequence[str], None] = 'cad8dee59dfe'
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
