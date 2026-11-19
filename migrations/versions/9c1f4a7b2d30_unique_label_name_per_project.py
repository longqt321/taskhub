"""unique label name per project

Revision ID: 9c1f4a7b2d30
Revises: 4b21c9d8e7a0
Create Date: 2026-11-19 17:47:00.000000

"""

from alembic import op

revision: str = "9c1f4a7b2d30"
down_revision: str | None = "4b21c9d8e7a0"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Trong một project, tên label không được trùng để client khỏi phải tự lọc.
    op.create_unique_constraint("uq_labels_project_id_name", "labels", ["project_id", "name"])


def downgrade() -> None:
    op.drop_constraint("uq_labels_project_id_name", "labels", type_="unique")
