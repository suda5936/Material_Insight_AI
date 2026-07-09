export interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface SnapshotImportResult {
  snapshot_id: number;
  project_id: number;
  label: string;
  activity_count: number;
  relationship_count: number;
  is_dag: boolean;
  warnings: string[];
}

export interface SnapshotSummary {
  id: number;
  project_id: number;
  label: string;
  imported_at: string;
  activity_count: number;
  relationship_count: number;
  is_dag: boolean | null;
}

export interface KnowledgeDocument {
  id: number;
  project_id: number;
  source_name: string;
  document_type: string;
  document_date: string;
  approval_status: string;
  trade: string;
  location: string;
  uploaded_at: string;
  chunk_count: number;
}

export interface Issue {
  id: number;
  project_id: number;
  raw_text: string;
  created_at: string;
}

export interface ActivityMatch {
  activity_id: string;
  name: string;
  sql_score: number;
  agent_confidence: number | null;
  agent_reason: string | null;
  rank: number;
  is_selected: boolean;
}

export interface Scenario {
  scenario_index: number;
  action: string;
  target_activity_id: string;
  reduction_days: number;
  adjusted_value_days: number;
  scenario_project_duration: number;
  recovered_days: number;
  applicable: boolean;
  rationale: string | null;
  evidence_chunk_ids: number[];
}

export interface ImpactJson {
  project_duration: number;
  project_delay_days: number;
  target_total_float: number;
  is_target_critical: boolean;
  critical_path: string[];
}

export interface RuleValidationJson {
  passed: boolean;
  requires_human_confirmation: boolean;
  violations: { code: string; message: string; details: Record<string, unknown> }[];
}

export interface ReviewJson {
  warnings: { category: string; message: string }[];
  needs_human_review: boolean;
  summary: string;
}

export interface AnalysisRun {
  id: number;
  issue_id: number;
  project_id: number;
  snapshot_id: number;
  status: string;
  selected_activity_id: string | null;
  issue_delay_days: number | null;
  impact_mode: string | null;
  retrieved_chunk_ids: number[];
  baseline_json: { project_duration: number; critical_path: string[] } | null;
  impact_json: ImpactJson | null;
  rule_validation_json: RuleValidationJson | null;
  review_json: ReviewJson | null;
  error_message: string | null;
  activity_matches: ActivityMatch[];
  scenarios: Scenario[];
  created_at: string;
  updated_at: string;
}

interface ApiErrorBody {
  error_code?: string;
  message?: string;
  detail?: string;
}

export class ApiError extends Error {
  code: string;
  constructor(message: string, code: string) {
    super(message);
    this.code = code;
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let body: ApiErrorBody = {};
    try {
      body = await response.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(
      body.message ?? body.detail ?? `Request failed (${response.status})`,
      body.error_code ?? "http_error",
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  listProjects: () => request<Project[]>("/api/v1/projects"),

  createProject: (name: string, description?: string) =>
    request<Project>("/api/v1/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: description ?? null }),
    }),

  listSnapshots: (projectId: number) =>
    request<SnapshotSummary[]>(`/api/v1/projects/${projectId}/snapshots`),

  importSnapshot: (projectId: number, label: string, activities: File, relationships: File) => {
    const form = new FormData();
    form.append("label", label);
    form.append("activities_csv", activities);
    form.append("relationships_csv", relationships);
    return request<SnapshotImportResult>(`/api/v1/projects/${projectId}/snapshots/import`, {
      method: "POST",
      body: form,
    });
  },

  listDocuments: (projectId: number) =>
    request<KnowledgeDocument[]>(`/api/v1/projects/${projectId}/knowledge/documents`),

  uploadDocument: (
    projectId: number,
    file: File,
    meta: {
      document_type: string;
      document_date: string;
      approval_status: string;
      trade: string;
      location: string;
    },
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", meta.document_type);
    form.append("document_date", meta.document_date);
    form.append("approval_status", meta.approval_status);
    form.append("trade", meta.trade);
    form.append("location", meta.location);
    return request<KnowledgeDocument>(`/api/v1/projects/${projectId}/knowledge/documents`, {
      method: "POST",
      body: form,
    });
  },

  createIssue: (projectId: number, rawText: string) =>
    request<Issue>("/api/v1/issues", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: projectId, raw_text: rawText }),
    }),

  analyzeIssue: (issueId: number) =>
    request<AnalysisRun>(`/api/v1/issues/${issueId}/analyze`, { method: "POST" }),

  selectActivity: (issueId: number, analysisRunId: number, activityId: string) =>
    request<AnalysisRun>(`/api/v1/issues/${issueId}/select-activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis_run_id: analysisRunId, activity_id: activityId }),
    }),

  getReportMarkdown: async (analysisRunId: number): Promise<string> => {
    const response = await fetch(`/api/v1/analysis-runs/${analysisRunId}/report.md`);
    if (!response.ok) {
      throw new ApiError("Report not found", "report_not_found");
    }
    return response.text();
  },
};
