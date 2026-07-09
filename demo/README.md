# P6 Schedule Recovery Copilot — 데모 실행 가이드

이 폴더는 발표/제출용 데모 패키지다.

```
demo/
├── activities.csv              # Activity 9개 (커튼월 시나리오)
├── relationships.csv           # FS 관계 9개
├── documents/                  # 현장 문서 3종 (RAG 근거)
│   ├── 01_커튼월_자재지연_통보.md
│   ├── 02_공정회의록.md
│   └── 03_커튼월_시공계획서.md
├── issue.txt                   # 자연어 지연 이슈
├── expected_output.md          # 기대 결과 (일정 수치는 고정)
└── alignment_checklist.md      # 설계-구현 일치도 체크리스트
```

## 0. 사전 준비

```bash
# 백엔드
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # (Windows Git Bash 기준)
# .env 작성: DATABASE_URL, OPENAI_API_KEY, VLLM_* 설정
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# 프론트엔드 (별도 터미널)
cd frontend
npm install
npm run dev            # http://localhost:5173  (/api → localhost:8000 프록시)
```

## 1. 프론트엔드로 시연 (권장)

1. 브라우저에서 http://localhost:5173 접속.
2. **1단계**: 새 프로젝트 생성 (예: "A현장 공동주택").
3. **2단계**: `demo/activities.csv`, `demo/relationships.csv` 업로드 → Import.
   - Activity 9 / Relationship 9 / DAG 정상 확인.
4. **3단계**: `demo/documents/`의 3개 문서를 업로드.
   - 각 문서 메타데이터 예시:
     | 파일 | 유형 | 날짜 | 승인 | 공종(trade) | 위치(location) |
     |---|---|---|---|---|---|
     | 01_커튼월_자재지연_통보.md | field_notice | 2026-07-03 | approved | curtain wall | A-12F |
     | 02_공정회의록.md | meeting_minutes | 2026-07-04 | approved | curtain wall | A-12F |
     | 03_커튼월_시공계획서.md | method_statement | 2026-06-20 | approved | curtain wall | A-12F |
5. **4단계**: `demo/issue.txt` 내용을 붙여넣고 "분석 실행".
   - Activity 매핑(A1050 상위), 자동 선택 또는 직접 선택.
   - CPM 영향(baseline 68 → impact 78, 지연 10), 복구 시나리오 3개(recovered days),
     규칙 검증, 독립 검토, Markdown 보고서를 확인.

## 2. API로 시연 (curl)

```bash
BASE=http://localhost:8000/api/v1

# 프로젝트 생성
PID=$(curl -s -X POST $BASE/projects -H "Content-Type: application/json" \
  -d '{"name":"A현장 공동주택"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 스냅샷 import
curl -s -X POST $BASE/projects/$PID/snapshots/import \
  -F "activities_csv=@demo/activities.csv;type=text/csv" \
  -F "relationships_csv=@demo/relationships.csv;type=text/csv" \
  -F "label=baseline"

# 문서 업로드 (예: 통보서)
curl -s -X POST $BASE/projects/$PID/knowledge/documents \
  -F "file=@demo/documents/01_커튼월_자재지연_통보.md;type=text/markdown" \
  -F "document_type=field_notice" -F "document_date=2026-07-03" \
  -F "approval_status=approved" -F "trade=curtain wall" -F "location=A-12F"

# 이슈 생성 + 분석
IID=$(curl -s -X POST $BASE/issues -H "Content-Type: application/json" \
  -d "{\"project_id\": $PID, \"raw_text\": \"A동 12층 커튼월 자재 납품이 10일 지연되어 설치 시작이 지연될 가능성이 있습니다.\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

RID=$(curl -s -X POST $BASE/issues/$IID/analyze | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# NEEDS_ACTIVITY_SELECTION이면 직접 선택
# curl -s -X POST $BASE/issues/$IID/select-activity -H "Content-Type: application/json" \
#   -d "{\"analysis_run_id\": $RID, \"activity_id\": \"A1050\"}"

# 보고서 확인
curl -s $BASE/analysis-runs/$RID/report.md
```

## 3. 기대 결과

`expected_output.md` 참고. 일정 수치(공기 68/78, 지연 10, recovered 10/5/6)는
결정론적으로 재현된다. LLM 문장 표현은 실행마다 달라질 수 있다.

> 참고(CLI 한정): Windows에서 `curl -F`로 **한글 파일명**을 업로드하면 멀티파트
> 파일명이 깨져 보고서의 source_name이 깨질 수 있다. 이는 curl/셸 인코딩 이슈이며
> 문서 내용·metadata·검색에는 영향이 없다. 프론트엔드(브라우저 FormData)로
> 업로드하면 한글 파일명도 정상 처리된다.

## 4. 참고: A1050 vs A1040 (human selection 시연)

커튼월 "설치(A1050)"와 "자재 납품(A1040)"은 모두 커튼월 공종이라 매핑 confidence가
비슷하게 나올 수 있다(예: 0.95 vs 0.85, margin < 0.10). 이 경우 시스템은
`NEEDS_ACTIVITY_SELECTION` 상태로 사람에게 선택을 요청하며, 설치 시작 지연이 핵심이므로
**A1050**를 선택하면 분석이 완료된다. 이는 human-in-the-loop 게이트가 의도대로
동작함을 보여주는 좋은 시연 포인트다.
