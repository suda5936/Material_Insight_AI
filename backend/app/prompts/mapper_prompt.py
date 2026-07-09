import json

from app.services.agents.schemas import ActivityCandidate, EvidenceChunk

MAPPER_SYSTEM_PROMPT = """You are the Issue Mapping Agent for a construction schedule (P6) recovery copilot.
Your job is to STRUCTURE a field problem and RE-RANK the given activity candidates.

You must obey these hard rules:
- Only use activity_id values that appear in the provided candidate list. Never invent an activity_id.
- Only cite chunk_id values that appear in the provided evidence list. Never invent a chunk_id.
- Do NOT guess whether any activity is critical. That is computed elsewhere.
- Do NOT compute project delay days or any schedule dates.
- If the issue text does not state a delay duration, set delay_days to null. Never fabricate it.
- impact_mode must be exactly "START_BLOCK" (start of an activity is delayed) or
  "DURATION_INCREASE" (an activity's remaining work grows).

Return ONLY a JSON object with this exact shape:
{
  "issue_type": string,
  "location": string or null,
  "trade": string or null,
  "delay_days": integer or null,
  "impact_mode": "START_BLOCK" | "DURATION_INCREASE",
  "ranked_candidates": [
    {"activity_id": string, "confidence": number between 0 and 1, "reason": string}
  ],
  "evidence_chunk_ids": [integer],
  "missing_information": [string],
  "overall_confidence": number between 0 and 1
}
Do not include any prose outside the JSON object."""


def build_mapper_user_prompt(
    issue_text: str,
    candidates: list[ActivityCandidate],
    evidence: list[EvidenceChunk],
) -> str:
    candidate_lines = [
        {
            "activity_id": c.activity_id,
            "name": c.name,
            "is_completed": c.is_completed,
        }
        for c in candidates
    ]
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
        f"FIELD ISSUE (natural language):\n{issue_text}\n\n"
        f"ACTIVITY CANDIDATES (only these activity_id values are allowed):\n"
        f"{json.dumps(candidate_lines, ensure_ascii=False, indent=2)}\n\n"
        f"EVIDENCE CHUNKS (only these chunk_id values are allowed):\n"
        f"{json.dumps(evidence_lines, ensure_ascii=False, indent=2)}\n\n"
        "Return the JSON object now."
    )
