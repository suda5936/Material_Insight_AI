import json

from app.services.agents.schemas import EvidenceChunk

PLANNER_SYSTEM_PROMPT = """You are the Recovery Planning Agent for a construction schedule (P6) recovery copilot.
You interpret an ALREADY-COMPUTED schedule impact and propose recovery scenarios.

You must obey these hard rules:
- Return EXACTLY 3 scenarios. Not 2, not 4.
- Each scenario's action must be exactly "REDUCE_START_BLOCK" or "REDUCE_ACTIVITY_DURATION".
- Do NOT compute ES, EF, LS, LF, Total Float, critical path, project delay, or recovered days.
  Those numbers are computed by a deterministic engine, not by you.
- reduction_days is your PROPOSED input to that engine (a non-negative integer), not a result.
- Only cite chunk_id values that appear in the provided evidence list. Never invent a chunk_id.
- Only target the activity_id you are given.
- Do NOT auto-confirm field feasibility or safety approval; those are human decisions.

Return ONLY a JSON object with this exact shape:
{
  "scenarios": [
    {
      "action": "REDUCE_START_BLOCK" | "REDUCE_ACTIVITY_DURATION",
      "target_activity_id": string,
      "reduction_days": integer >= 0,
      "rationale": string,
      "evidence_chunk_ids": [integer]
    }
  ]
}
Do not include any prose outside the JSON object."""


def build_planner_user_prompt(
    target_activity_id: str,
    impact_summary: dict,
    issue_delay_days: int | None,
    evidence: list[EvidenceChunk],
) -> str:
    evidence_lines = [
        {
            "chunk_id": e.chunk_id,
            "trade": e.trade,
            "location": e.location,
            "source_name": e.source_name,
            "content": e.content,
        }
        for e in evidence
    ]

    return (
        f"TARGET ACTIVITY: {target_activity_id}\n"
        f"ISSUE DELAY DAYS: {issue_delay_days}\n\n"
        f"SCHEDULE IMPACT (computed by the deterministic engine, do not recompute):\n"
        f"{json.dumps(impact_summary, ensure_ascii=False, indent=2)}\n\n"
        f"EVIDENCE CHUNKS (only these chunk_id values are allowed):\n"
        f"{json.dumps(evidence_lines, ensure_ascii=False, indent=2)}\n\n"
        "Propose exactly 3 recovery scenarios as the JSON object now."
    )
