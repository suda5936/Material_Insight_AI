import { useState } from "react";
import { api, ApiError, type AnalysisRun } from "../api";

interface Props {
  projectId: number;
  initialIssue?: string;
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "COMPLETED" ? "ok" : status === "FAILED" ? "danger" : status === "NEEDS_ACTIVITY_SELECTION" ? "warn" : "info";
  return <span className={`badge ${cls}`}>{status}</span>;
}

export function AnalysisStep({ projectId, initialIssue = "" }: Props) {
  const [issueText, setIssueText] = useState(initialIssue);
  const [issueId, setIssueId] = useState<number | null>(null);
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [report, setReport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadReport(analysisRunId: number) {
    try {
      setReport(await api.getReportMarkdown(analysisRunId));
    } catch {
      setReport(null);
    }
  }

  async function analyze() {
    if (!issueText.trim()) return;
    setLoading(true);
    setError(null);
    setReport(null);
    setRun(null);
    try {
      const issue = await api.createIssue(projectId, issueText.trim());
      setIssueId(issue.id);
      const result = await api.analyzeIssue(issue.id);
      setRun(result);
      await loadReport(result.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function choose(activityId: string) {
    if (!issueId || !run) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.selectActivity(issueId, run.id, activityId);
      setRun(result);
      await loadReport(result.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const needsSelection = run?.status === "NEEDS_ACTIVITY_SELECTION";
  const impact = run?.impact_json;

  return (
    <section className="step">
      <h2>
        <span className="num">4</span> 지연 이슈 분석
      </h2>

      <label>현장 문제 (자연어)</label>
      <textarea
        value={issueText}
        onChange={(e) => setIssueText(e.target.value)}
        placeholder="예: A동 12층 커튼월 자재 납품이 10일 지연되어 설치 시작이 지연될 가능성이 있습니다."
      />
      <button onClick={() => void analyze()} disabled={loading || !issueText.trim()}>
        {loading ? "분석 중..." : "분석 실행"}
      </button>

      {error && <div className="notice error">{error}</div>}

      {run && (
        <>
          <div style={{ marginTop: 16, marginBottom: 8 }}>
            분석 상태: <StatusBadge status={run.status} />
            {run.impact_mode && <span className="badge info" style={{ marginLeft: 8 }}>{run.impact_mode}</span>}
            {run.issue_delay_days != null && (
              <span className="badge info" style={{ marginLeft: 8 }}>지연 {run.issue_delay_days}일</span>
            )}
          </div>

          {run.error_message && <div className="notice error">{run.error_message}</div>}

          {needsSelection && (
            <div className="notice warn">
              자동 선택 조건을 만족하지 못했습니다. 아래에서 Activity를 직접 선택하세요 (행 클릭).
            </div>
          )}

          {run.activity_matches.length > 0 && (
            <>
              <h3 style={{ fontSize: 14, marginTop: 16 }}>Activity 매핑 후보</h3>
              <table>
                <thead>
                  <tr>
                    <th>Activity</th>
                    <th>이름</th>
                    <th>SQL score</th>
                    <th>Agent conf.</th>
                    <th>선택</th>
                  </tr>
                </thead>
                <tbody>
                  {run.activity_matches.map((m) => (
                    <tr
                      key={m.activity_id}
                      className={`${needsSelection ? "selectable-row" : ""} ${m.is_selected ? "chosen" : ""}`}
                      onClick={() => needsSelection && void choose(m.activity_id)}
                    >
                      <td>{m.activity_id}</td>
                      <td>{m.name}</td>
                      <td>{m.sql_score.toFixed(3)}</td>
                      <td>{m.agent_confidence == null ? "-" : m.agent_confidence.toFixed(2)}</td>
                      <td>
                        {m.is_selected ? (
                          <span className="badge ok">선택됨</span>
                        ) : needsSelection ? (
                          <span className="badge info">클릭</span>
                        ) : (
                          ""
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {impact && (
            <>
              <h3 style={{ fontSize: 14, marginTop: 18 }}>일정 영향 (CPM)</h3>
              <div className="pill-row">
                <div className="stat">
                  <div className="k">baseline 기간</div>
                  <div className="v">{run.baseline_json?.project_duration ?? "-"}</div>
                </div>
                <div className="stat">
                  <div className="k">impact 기간</div>
                  <div className="v">{impact.project_duration}</div>
                </div>
                <div className="stat">
                  <div className="k">프로젝트 지연</div>
                  <div className="v">{impact.project_delay_days}</div>
                </div>
                <div className="stat">
                  <div className="k">대상 Float</div>
                  <div className="v">{impact.target_total_float}</div>
                </div>
                <div className="stat">
                  <div className="k">critical</div>
                  <div className="v">{impact.is_target_critical ? "예" : "아니오"}</div>
                </div>
              </div>
              {impact.critical_path.length > 0 && (
                <p className="muted">Critical Path: {impact.critical_path.join(" → ")}</p>
              )}
            </>
          )}

          {run.scenarios.length > 0 && (
            <>
              <h3 style={{ fontSize: 14, marginTop: 18 }}>복구 시나리오 비교</h3>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>action</th>
                    <th>reduction</th>
                    <th>시나리오 기간</th>
                    <th>recovered</th>
                    <th>적용</th>
                  </tr>
                </thead>
                <tbody>
                  {run.scenarios.map((s) => (
                    <tr key={s.scenario_index}>
                      <td>{s.scenario_index + 1}</td>
                      <td>{s.action}</td>
                      <td>{s.reduction_days}</td>
                      <td>{s.scenario_project_duration}</td>
                      <td>
                        <strong>{s.recovered_days}일</strong>
                      </td>
                      <td>{s.applicable ? "✅" : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {run.rule_validation_json && (
            <div className={`notice ${run.rule_validation_json.passed ? "ok" : "warn"}`}>
              규칙 검증: {run.rule_validation_json.passed ? "통과" : "위반 있음"} · human confirmation 필요:{" "}
              {run.rule_validation_json.requires_human_confirmation ? "예" : "아니오"}
              {run.rule_validation_json.violations.map((v, i) => (
                <div key={i}>• {v.code}: {v.message}</div>
              ))}
            </div>
          )}

          {run.review_json && (
            <div className={`notice ${run.review_json.needs_human_review ? "warn" : "ok"}`}>
              <strong>독립 검토:</strong> {run.review_json.summary}
              {run.review_json.warnings.map((w, i) => (
                <div key={i}>• [{w.category}] {w.message}</div>
              ))}
            </div>
          )}

          {run.status === "COMPLETED" && (
            <div className="notice info">
              최종 판단(P6 반영, 시나리오 선택, safety/quality/cost 승인, contract/EOT)은 사람이 결정합니다.
            </div>
          )}

          {report && (
            <>
              <h3 style={{ fontSize: 14, marginTop: 18 }}>Markdown 보고서</h3>
              <div className="report">{report}</div>
            </>
          )}
        </>
      )}
    </section>
  );
}
