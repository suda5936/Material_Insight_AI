// 저장소 루트 demo/ 폴더의 파일들을 빌드 시점에 문자열로 인라인한다(?raw).
// git clone 하면 demo/도 함께 받으므로, 별도 복사본 없이 이 단일 소스를 그대로 사용한다.
import activitiesCsv from "../../demo/activities.csv?raw";
import relationshipsCsv from "../../demo/relationships.csv?raw";
import issueText from "../../demo/issue.txt?raw";
import doc01 from "../../demo/documents/01_커튼월_자재지연_통보.md?raw";
import doc02 from "../../demo/documents/02_공정회의록.md?raw";
import doc03 from "../../demo/documents/03_커튼월_시공계획서.md?raw";

export interface DemoDoc {
  filename: string;
  content: string;
  document_type: string;
  document_date: string;
  approval_status: string;
  trade: string;
  location: string;
}

export const demoDataset = {
  projectName: "A현장 공동주택 데모",
  projectDescription: "커튼월 자재 지연 시나리오 (자동 로드된 데모 데이터셋)",
  snapshotLabel: "baseline",
  activitiesCsv,
  relationshipsCsv,
  issueText: issueText.trim(),
  documents: [
    {
      filename: "01_커튼월_자재지연_통보.md",
      content: doc01,
      document_type: "field_notice",
      document_date: "2026-07-03",
      approval_status: "approved",
      trade: "curtain wall",
      location: "A-12F",
    },
    {
      filename: "02_공정회의록.md",
      content: doc02,
      document_type: "meeting_minutes",
      document_date: "2026-07-04",
      approval_status: "approved",
      trade: "curtain wall",
      location: "A-12F",
    },
    {
      filename: "03_커튼월_시공계획서.md",
      content: doc03,
      document_type: "method_statement",
      document_date: "2026-06-20",
      approval_status: "approved",
      trade: "curtain wall",
      location: "A-12F",
    },
  ] as DemoDoc[],
};
