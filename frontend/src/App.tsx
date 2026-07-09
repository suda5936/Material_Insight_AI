import { useState } from "react";
import type { Project } from "./api";
import { DemoLoader } from "./components/DemoLoader";
import { ProjectStep } from "./components/ProjectStep";
import { SnapshotStep } from "./components/SnapshotStep";
import { KnowledgeStep } from "./components/KnowledgeStep";
import { AnalysisStep } from "./components/AnalysisStep";

export function App() {
  const [project, setProject] = useState<Project | null>(null);
  // 스냅샷이 준비됐는지(이번 세션 업로드 or 기존 스냅샷 존재) 여부.
  const [snapshotReady, setSnapshotReady] = useState(false);
  // 데모 로더가 채워주는 초기 이슈 텍스트(4단계 프리필).
  const [initialIssue, setInitialIssue] = useState("");

  return (
    <div className="app">
      <header className="app-header">
        <h1>P6 Schedule Recovery Copilot</h1>
        <p>
          현장 지연 문제를 입력하면 Critical Path 영향과 복구 대안 3개, 근거 문서가 연결된 분석 보고서를 제공합니다.
          (일정 계산은 결정론적 엔진, 최종 판단은 사람이 수행)
        </p>
      </header>

      <DemoLoader
        onLoaded={(p, issue) => {
          setProject(p);
          setSnapshotReady(true);
          setInitialIssue(issue);
        }}
      />

      <ProjectStep
        selectedProject={project}
        onSelect={(p) => {
          setProject(p);
          setSnapshotReady(false);
          setInitialIssue("");
        }}
      />

      {project ? (
        <SnapshotStep projectId={project.id} onReady={() => setSnapshotReady(true)} />
      ) : (
        <section className="step disabled">
          <h2>
            <span className="num">2</span> 일정 스냅샷 Import
          </h2>
          <p className="muted">먼저 프로젝트를 선택하세요.</p>
        </section>
      )}

      {project && <KnowledgeStep projectId={project.id} />}

      {project && snapshotReady ? (
        <AnalysisStep key={project.id} projectId={project.id} initialIssue={initialIssue} />
      ) : (
        <section className="step disabled">
          <h2>
            <span className="num">4</span> 지연 이슈 분석
          </h2>
          <p className="muted">
            프로젝트를 선택하고 스냅샷이 준비되면(신규 import 또는 기존 스냅샷) 분석을 실행할 수 있습니다.
          </p>
        </section>
      )}
    </div>
  );
}
