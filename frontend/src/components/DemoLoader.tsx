import { useState } from "react";
import { api, ApiError, type Project } from "../api";
import { demoDataset } from "../demoData";

interface Props {
  onLoaded: (project: Project, issueText: string) => void;
}

function textFile(name: string, content: string, type: string): File {
  return new File([content], name, { type });
}

export function DemoLoader({ onLoaded }: Props) {
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadDemo() {
    setLoading(true);
    setError(null);
    try {
      // 매번 새 프로젝트로 생성해 기존 데이터와 충돌하지 않게 한다.
      const stamp = new Date().toLocaleString("ko-KR");
      setStatus("프로젝트 생성 중...");
      const project = await api.createProject(
        `${demoDataset.projectName} (${stamp})`,
        demoDataset.projectDescription,
      );

      setStatus("일정 스냅샷(CSV) import 중...");
      await api.importSnapshot(
        project.id,
        demoDataset.snapshotLabel,
        textFile("activities.csv", demoDataset.activitiesCsv, "text/csv"),
        textFile("relationships.csv", demoDataset.relationshipsCsv, "text/csv"),
      );

      for (const doc of demoDataset.documents) {
        setStatus(`현장 문서 업로드 중... (${doc.filename})`);
        await api.uploadDocument(project.id, textFile(doc.filename, doc.content, "text/markdown"), {
          document_type: doc.document_type,
          document_date: doc.document_date,
          approval_status: doc.approval_status,
          trade: doc.trade,
          location: doc.location,
        });
      }

      setStatus("완료! 아래 4단계에서 바로 분석을 실행하세요.");
      onLoaded(project, demoDataset.issueText);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="step">
      <h2>
        <span className="num">★</span> 데모 데이터 한 번에 불러오기
      </h2>
      <p className="muted">
        저장소의 <code>demo/</code> 데이터셋(Activity/Relationship CSV + 현장 문서 3종)을 자동으로
        프로젝트에 적재합니다. 처음 테스트하는 분은 이 버튼 하나면 4단계 분석까지 바로 진행할 수 있습니다.
      </p>
      <button onClick={() => void loadDemo()} disabled={loading}>
        {loading ? "불러오는 중..." : "데모 데이터 불러오기"}
      </button>
      {status && <div className="notice ok">{status}</div>}
      {error && <div className="notice error">{error}</div>}
    </section>
  );
}
