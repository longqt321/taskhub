"""add workspaces projects labels and task fields

Revision ID: 4b21c9d8e7a0
Revises: 73896faec423
Create Date: 2026-11-17 14:53:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision: str = "4b21c9d8e7a0"
down_revision: str | None = "73896faec423"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_owner_id"), "workspaces", ["owner_id"], unique=False)

    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            sa.Enum(
                "OWNER",
                "EDITOR",
                "VIEWER",
                name="workspace_role",
                native_enum=False,
                length=20,
            ),
            name="role",
            nullable=False,
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("workspace_id", "user_id"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            sa.Enum(
                "ACTIVE",
                "ARCHIVED",
                name="project_status",
                native_enum=False,
                length=20,
            ),
            name="status",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_workspace_id"), "projects", ["workspace_id"], unique=False)

    op.create_table(
        "labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_labels_project_id"), "labels", ["project_id"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comments_task_id"), "comments", ["task_id"], unique=False)
    op.create_index(op.f("ix_comments_author_id"), "comments", ["author_id"], unique=False)

    op.create_table(
        "task_labels",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "label_id"),
    )

    op.add_column(
        "tasks", sa.Column("project_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "tasks", sa.Column("assignee_id", sa.Uuid(), nullable=True)
    )
    op.add_column("tasks", sa.Column("created_by", sa.Uuid(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column(
            sa.Enum(
                "LOW",
                "MEDIUM",
                "HIGH",
                "URGENT",
                name="task_priority",
                native_enum=False,
                length=20,
            ),
            name="priority",
            nullable=True,
        ),
    )
    op.add_column("tasks", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))

    # Day 1-3 chưa có project nên task cũ không có chỗ để gán. Schema Day 4 không cho
    # project_id null, xoá mấy bản ghi thử nghiệm đó trước khi siết lại ràng buộc.
    op.execute("DELETE FROM tasks")
    op.alter_column("tasks", "project_id", nullable=False)
    op.alter_column("tasks", "created_by", nullable=False)
    op.alter_column("tasks", "priority", nullable=False, server_default="MEDIUM")
    op.alter_column("tasks", "priority", server_default=None)

    op.create_foreign_key(
        "fk_tasks_project_id_projects", "tasks", "projects", ["project_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_tasks_assignee_id_users", "tasks", "users", ["assignee_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tasks_created_by_users", "tasks", "users", ["created_by"], ["id"]
    )
    op.create_index(op.f("ix_tasks_project_id"), "tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_tasks_created_by"), "tasks", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_created_by"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_assignee_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_project_id"), table_name="tasks")
    op.drop_constraint("fk_tasks_created_by_users", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_assignee_id_users", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_project_id_projects", "tasks", type_="foreignkey")
    op.drop_column("tasks", "due_date")
    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "created_by")
    op.drop_column("tasks", "assignee_id")
    op.drop_column("tasks", "project_id")

    op.drop_table("task_labels")
    op.drop_index(op.f("ix_comments_author_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_task_id"), table_name="comments")
    op.drop_table("comments")
    op.drop_index(op.f("ix_labels_project_id"), table_name="labels")
    op.drop_table("labels")
    op.drop_index(op.f("ix_projects_workspace_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_table("workspace_members")
    op.drop_index(op.f("ix_workspaces_owner_id"), table_name="workspaces")
    op.drop_table("workspaces")
