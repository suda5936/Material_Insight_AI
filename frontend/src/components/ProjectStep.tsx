import { useEffect, useState } from "react";
import { api, ApiError, type Project } from "../api";

interface Props {
  selectedProject: Project | null;
  onSelect: (project: Project) => void;
}

export function ProjectStep({ selectedProject, onSelect }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    try {
      setProjects(await api.listProjects());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function create() {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const project = await api.createProject(name.trim());
      setName("");
      await refresh();
      onSelect(project);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="step">
      <h2>
        <span className="num">1</span> 프로젝트 선택 / 생성
      </h2>

      <label>기존 프로젝트</label>
      <select
        value={selectedProject?.id ?? ""}
        onChange={(e) => {
          const p = projects.find((x) => x.id === Number(e.target.value));
          if (p) onSelect(p);
        }}
      >
        <option value="" disabled>
          프로젝트를 선택하세요
        </option>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name} (#{p.id})
          </option>
        ))}
      </select>

      <div className="row" style={{ alignItems: "flex-end", marginTop: 12 }}>
        <div>
          <label>새 프로젝트 이름</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="예: A현장 공동주택" />
        </div>
        <div style={{ flex: "0 0 auto" }}>
          <button onClick={() => void create()} disabled={loading || !name.trim()}>
            생성
          </button>
        </div>
      </div>

      {selectedProject && (
        <div className="notice ok">
          선택됨: <strong>{selectedProject.name}</strong> (#{selectedProject.id})
        </div>
      )}
      {error && <div className="notice error">{error}</div>}
    </section>
  );
}
