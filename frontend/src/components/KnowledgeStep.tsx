import { useEffect, useState } from "react";
import { api, ApiError, type KnowledgeDocument } from "../api";

interface Props {
  projectId: number;
}

const today = new Date().toISOString().slice(0, 10);

export function KnowledgeStep({ projectId }: Props) {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [meta, setMeta] = useState({
    document_type: "field_notice",
    document_date: today,
    approval_status: "approved",
    trade: "",
    location: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    try {
      setDocs(await api.listDocuments(projectId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
  }, [projectId]);

  async function upload() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      await api.uploadDocument(projectId, file, meta);
      setFile(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="step">
      <h2>
        <span className="num">3</span> 현장 문서 업로드 (TXT / MD) · 선택 사항
      </h2>
      <p className="muted">근거 문서를 올리면 RAG가 분석 보고서에 근거를 연결합니다. 없어도 분석은 가능합니다.</p>

      <div className="grid-2">
        <div>
          <label>문서 파일 (.txt / .md)</label>
          <input type="file" accept=".txt,.md" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <div>
          <label>문서 유형</label>
          <input
            value={meta.document_type}
            onChange={(e) => setMeta({ ...meta, document_type: e.target.value })}
          />
        </div>
        <div>
          <label>날짜 (YYYY-MM-DD)</label>
          <input value={meta.document_date} onChange={(e) => setMeta({ ...meta, document_date: e.target.value })} />
        </div>
        <div>
          <label>승인 상태</label>
          <select
            value={meta.approval_status}
            onChange={(e) => setMeta({ ...meta, approval_status: e.target.value })}
          >
            <option value="approved">approved</option>
            <option value="pending">pending</option>
            <option value="draft">draft</option>
            <option value="rejected">rejected</option>
          </select>
        </div>
        <div>
          <label>공종 (trade)</label>
          <input value={meta.trade} onChange={(e) => setMeta({ ...meta, trade: e.target.value })} />
        </div>
        <div>
          <label>위치 (location)</label>
          <input value={meta.location} onChange={(e) => setMeta({ ...meta, location: e.target.value })} />
        </div>
      </div>

      <button onClick={() => void upload()} disabled={loading || !file}>
        업로드
      </button>

      {docs.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>파일</th>
              <th>유형</th>
              <th>공종</th>
              <th>위치</th>
              <th>chunk</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.id}</td>
                <td>{d.source_name}</td>
                <td>{d.document_type}</td>
                <td>{d.trade}</td>
                <td>{d.location}</td>
                <td>{d.chunk_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {error && <div className="notice error">{error}</div>}
    </section>
  );
}
