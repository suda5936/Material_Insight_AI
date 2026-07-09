"""Phase 2 schedule data tables: projects, schedule_snapshots, activities, relationships.

Revision ID: 0001_schedule_data
Revises:
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_schedule_data"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "schedule_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activity_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relationship_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_dag", sa.Boolean(), nullable=True),
        sa.Column("cycle_activity_ids", sa.String(length=4000), nullable=True),
    )
    op.create_index(
        "ix_schedule_snapshots_project_id", "schedule_snapshots", ["project_id"]
    )

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.Integer(),
            sa.ForeignKey("schedule_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("activity_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("original_duration", sa.Integer(), nullable=False),
        sa.Column("remaining_duration", sa.Integer(), nullable=False),
        sa.Column("is_milestone", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint(
            "snapshot_id", "activity_id", name="uq_activity_snapshot_activity_id"
        ),
    )
    op.create_index("ix_activities_snapshot_id", "activities", ["snapshot_id"])

    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.Integer(),
            sa.ForeignKey("schedule_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("predecessor_id", sa.String(length=50), nullable=False),
        sa.Column("successor_id", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=2), nullable=False),
        sa.Column("lag", sa.Integer(), nullable=False),
    )
    op.create_index("ix_relationships_snapshot_id", "relationships", ["snapshot_id"])


def downgrade() -> None:
    op.drop_index("ix_relationships_snapshot_id", table_name="relationships")
    op.drop_table("relationships")
    op.drop_index("ix_activities_snapshot_id", table_name="activities")
    op.drop_table("activities")
    op.drop_index("ix_schedule_snapshots_project_id", table_name="schedule_snapshots")
    op.drop_table("schedule_snapshots")
    op.drop_table("projects")
