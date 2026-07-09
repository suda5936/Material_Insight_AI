import { useEffect, useState } from "react";
import { api, ApiError, type SnapshotImportResult, type SnapshotSummary } from "../api";

interface Props {
  projectId: number;
  onReady: () => void;
}

export function SnapshotStep({ projectId, onReady }: Props) {
  const [label, setLabel] = useState("baseline");
  const [activities, setActivities] = useState<File | null>(null);
  const [relationships, setRelationships] = useState<File | null>(null);
  const [result, setResult] = useState<SnapshotImportResult | null>(null);
  const [existing, setExisting] = useState<SnapshotSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 프로젝트에 이미 스냅샷이 있으면(=이전에 import 완료) 재업로드 없이 분석을 열어준다.
  useEffect(() => {
    void (async () => {
      try {
        const snaps = await api.listSnapshots(projectId);
        setExisting(snaps);
        if (snaps.length > 0) onReady();
      } catch {
        /* ignore */
      }
    })();
  }, [projectId]);

  async function submit() {
    if (!activities || !relationships) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.importSnapshot(projectId, label.trim() || "baseline", activities, relationships);
      setResult(res);
      setExisting(await api.listSnapshots(projectId));
      onReady();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="step">
      <h2>
        <span className="num">2</span> 일정 스냅샷 Import (Activity / Relationship CSV)
      </h2>

      {existing.length > 0 && (
        <div className="notice ok">
          이미 스냅샷 {existing.length}개가 있습니다 (예: "{existing[0].label}", Activity{" "}
          {existing[0].activity_count}개). 재업로드 없이 아래 4단계에서 바로 분석할 수 있습니다.
          <br />
          <span className="muted">
            새 CSV를 올리면 새 스냅샷이 추가되며, 분석은 항상 가장 최근 스냅샷을 사용합니다.
          </span>
        </div>
      )}

      <label>스냅샷 라벨</label>
      <input value={label} onChange={(e) => setLabel(e.target.value)} />

      <div className="grid-2" style={{ marginTop: 8 }}>
        <div>
          <label>Activity CSV</label>
          <input type="file" accept=".csv" onChange={(e) => setActivities(e.target.files?.[0] ?? null)} />
        </div>
        <div>
          <label>Relationship CSV</label>
          <input type="file" accept=".csv" onChange={(e) => setRelationships(e.target.files?.[0] ?? null)} />
        </div>
      </div>

      <button onClick={() => void submit()} disabled={loading || !activities || !relationships}>
        Import
      </button>

      {result && (
        <div className={`notice ${result.is_dag ? "ok" : "warn"}`}>
          Activity {result.activity_count}개, Relationship {result.relationship_count}개 import 완료. DAG:{" "}
          {result.is_dag ? "정상" : "순환 존재"}
          {result.warnings.map((w, i) => (
            <div key={i}>⚠️ {w}</div>
          ))}
        </div>
      )}
      {error && <div className="notice error">{error}</div>}
    </section>
  );
}
