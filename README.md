# P6 Schedule Recovery Copilot

This workspace is being rebuilt around the uploaded P6 Schedule Recovery Copilot blueprint and final report.

The MVP goal is:

```text
When a critical path delay occurs during construction, help the schedule manager identify the affected activity, calculate deterministic schedule impact, compare three recovery scenarios, and draft a human-reviewed recovery report before any P6 update.
```

The copilot is not an automatic P6 writer. It prepares analysis, evidence, scenarios, validation checks, and report drafts so a human scheduler can make the final decision.

## Core MVP Flow

```text
Project
-> Activity CSV import
-> Relationship CSV import
-> Field document import
-> Issue intake
-> Activity mapping
-> RAG evidence retrieval
-> CPM impact calculation
-> Three recovery scenarios
-> Rule validation
-> Review
-> Human confirmation
-> Markdown report
```

## Design Rules

- LLMs interpret, draft, and review.
- Python code performs ES, EF, LS, LF, Total Float, critical path, delay, and recovered-day calculations.
- RAG supplies supporting evidence only; it does not calculate schedule impact.
- MVP supports FS relationships, non-negative integer lag, integer calendar-day durations, and a 7-day project calendar assumption.
- The system never writes directly to live P6 in the MVP.
- Human approval remains required for schedule, safety, quality, cost, contract, and recovery decisions.

## Preserved Optional Module

Rhino object detection and object selection are preserved as a separate optional context module:

```text
modules/rhino-object-sync/
```

Its new role is not material review. It is an optional visual context selector for construction issues.

Example:

```text
Select affected Rhino object
-> attach object_id / layer / bbox / location context to CP delay event
-> analyze schedule impact using schedule data
```

## Important Documents

- `docs/p6-schedule-recovery-copilot-integrated-ko.md`
- `docs/p6-schedule-recovery-copilot-phase-summary-ko.md`
- `modules/rhino-object-sync/README.md`
- `reports/p6-blueprint-restart-phase-1-report.md`

## Existing Runtime Areas

```text
backend/                     FastAPI backend
frontend/mock-plugin-ui/     Current browser UI, to be rebuilt around CP recovery
plugin/RhinoMaterialInsight/ Preserved Rhino plugin implementation
docs/                        Current P6 Copilot implementation documents
reports/                     Current phase reports
```

## Next Implementation Direction

1. Keep Rhino sync endpoints and plugin commands stable as optional context.
2. Implement the backend foundation from the P6 blueprint.
3. Add project, schedule snapshot, activity, and relationship imports.
4. Add deterministic CPM and recovery simulation.
5. Add project-scoped RAG and evidence validation.
6. Add mapper, planner, validator, reviewer, orchestration, and report generation.
