"""Phase 7 orchestration tables: issues, analysis_runs, activity_matches,
scenario_runs, agent_runs, reports (+ retrieval_runs link, pg_trgm).

Revision ID: 0003_analysis_orchestration
Revises: 0002_knowledge_rag
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_analysis_orchestration"
down_revision = "0002_knowledge_rag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_issues_project_id", "issues", ["project_id"])

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), sa.ForeignKey("schedule_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("selected_activity_id", sa.String(length=50), nullable=True),
        sa.Column("issue_delay_days", sa.Integer(), nullable=True),
        sa.Column("impact_mode", sa.String(length=20), nullable=True),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=True),
        sa.Column("mapping_json", sa.JSON(), nullable=True),
        sa.Column("plan_json", sa.JSON(), nullable=True),
        sa.Column("rule_validation_json", sa.JSON(), nullable=True),
        sa.Column("review_json", sa.JSON(), nullable=True),
        sa.Column("baseline_json", sa.JSON(), nullable=True),
        sa.Column("impact_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_runs_issue_id", "analysis_runs", ["issue_id"])

    op.add_column(
        "retrieval_runs",
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True),
    )

    op.create_table(
        "activity_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("sql_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("agent_confidence", sa.Float(), nullable=True),
        sa.Column("agent_reason", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_activity_matches_analysis_run_id", "activity_matches", ["analysis_run_id"])

    op.create_table(
        "scenario_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_index", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("target_activity_id", sa.String(length=50), nullable=False),
        sa.Column("reduction_days", sa.Integer(), nullable=False),
        sa.Column("adjusted_value_days", sa.Integer(), nullable=False),
        sa.Column("scenario_project_duration", sa.Integer(), nullable=False),
        sa.Column("recovered_days", sa.Integer(), nullable=False),
        sa.Column("applicable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("evidence_chunk_ids", sa.JSON(), nullable=True),
    )
    op.create_index("ix_scenario_runs_analysis_run_id", "scenario_runs", ["analysis_run_id"])

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_role", sa.String(length=40), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("raw_output", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_runs_analysis_run_id", "agent_runs", ["analysis_run_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    if is_postgres:
        op.execute(
            "CREATE INDEX ix_activities_name_trgm ON activities USING gin (name gin_trgm_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_activities_name_trgm")

    op.drop_table("reports")
    op.drop_index("ix_agent_runs_analysis_run_id", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index("ix_scenario_runs_analysis_run_id", table_name="scenario_runs")
    op.drop_table("scenario_runs")
    op.drop_index("ix_activity_matches_analysis_run_id", table_name="activity_matches")
    op.drop_table("activity_matches")
    op.drop_column("retrieval_runs", "analysis_run_id")
    op.drop_index("ix_analysis_runs_issue_id", table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index("ix_issues_project_id", table_name="issues")
    op.drop_table("issues")
