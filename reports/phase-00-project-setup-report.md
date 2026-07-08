# Phase 00 Report: 프로젝트 골격 및 기준 고정

## 1. Phase 목표

Phase 0의 목표는 Material Insight AI MVP 구현을 시작하기 위한 기본 작업공간을 구성하는 것이다.

이번 phase에서는 실제 구현 산출물과 과제 설명 문서를 분리하고, 이후 phase별 작업 결과를 일관되게 기록할 수 있도록 README와 report 템플릿을 준비했다.

## 2. 수행 작업

- 구현용 루트 폴더 구조를 생성했다.
- `backend/`, `data/`, `frontend/mock-plugin-ui/`, `plugin/`, `infra/`, `docs/`, `reports/` 영역을 분리했다.
- FastAPI 백엔드가 들어갈 `backend/app` 하위 구조를 미리 생성했다.
- Rhino Plugin skeleton을 위한 `plugin/RhinoMaterialInsight` 하위 구조를 미리 생성했다.
- 샘플 객체, 규칙, 문서 데이터가 들어갈 `data/` 하위 구조를 미리 생성했다.
- 루트 `README.md`를 작성해 프로젝트 목표, 구현 범위, 제외 범위, phase 운영 원칙을 정리했다.
- phase별 보고서 작성을 위한 공통 템플릿을 생성했다.

## 3. 생성/수정 파일

| 파일 | 설명 |
|---|---|
| `README.md` | 구현 프로젝트의 목표, 구조, phase 운영 원칙, MVP 흐름 정리 |
| `backend/.gitkeep` | 백엔드 루트 placeholder |
| `backend/app/.gitkeep` | FastAPI 앱 루트 placeholder |
| `backend/app/api/.gitkeep` | API route 영역 placeholder |
| `backend/app/core/.gitkeep` | 설정, 로깅 등 core 영역 placeholder |
| `backend/app/db/.gitkeep` | DB 연결 및 schema 영역 placeholder |
| `backend/app/models/.gitkeep` | Pydantic model 영역 placeholder |
| `backend/app/prompts/.gitkeep` | LLM prompt 영역 placeholder |
| `backend/app/services/.gitkeep` | Rule/RAG/LLM service 영역 placeholder |
| `backend/app/tests/.gitkeep` | 테스트 영역 placeholder |
| `data/sample_objects/.gitkeep` | 샘플 Rhino/CAD 객체 JSON 저장 위치 |
| `data/rules/.gitkeep` | YAML 규칙 파일 저장 위치 |
| `data/documents/specs/.gitkeep` | 샘플 시방서 저장 위치 |
| `data/documents/catalogs/.gitkeep` | 샘플 카탈로그 저장 위치 |
| `data/documents/standards/.gitkeep` | 샘플 기준 문서 저장 위치 |
| `docs/.gitkeep` | 구현 중 생성되는 API/데모 문서 저장 위치 |
| `frontend/mock-plugin-ui/.gitkeep` | Rhino 없이 시연 가능한 UI 구현 위치 |
| `infra/.gitkeep` | Docker, DB 등 인프라 설정 위치 |
| `plugin/RhinoMaterialInsight/.gitkeep` | Rhino Plugin skeleton 루트 |
| `plugin/RhinoMaterialInsight/Commands/.gitkeep` | Rhino command 구현 위치 |
| `plugin/RhinoMaterialInsight/Models/.gitkeep` | Plugin model 구현 위치 |
| `plugin/RhinoMaterialInsight/Panels/.gitkeep` | Rhino panel 구현 위치 |
| `plugin/RhinoMaterialInsight/Services/.gitkeep` | Object inspector/API client 구현 위치 |
| `reports/_phase-report-template.md` | phase report 공통 템플릿 |
| `reports/phase-00-project-setup-report.md` | Phase 0 작업 보고서 |

## 4. 검증 결과

Phase 0은 실행 가능한 코드 구현 전 단계이므로, 검증은 구조 확인 중심으로 수행했다.

확인한 내용:

- 루트에 실제 구현용 `README.md`가 생성되었다.
- 구현용 폴더와 설명 문서 폴더가 분리되었다.
- `reports/` 폴더에 공통 템플릿과 Phase 0 report가 생성되었다.
- `backend/app` 하위에 Phase 1에서 사용할 기본 영역이 준비되었다.
- `data/` 하위에 Phase 2와 Phase 3에서 사용할 샘플 객체, 규칙, 문서 위치가 준비되었다.
- `plugin/RhinoMaterialInsight` 하위에 Phase 9에서 사용할 Rhino Plugin skeleton 위치가 준비되었다.

## 5. 설계 문서와의 일치 여부

이번 phase는 다음 문서와 직접 연결된다.

| 설계 문서 | 반영 내용 |
|---|---|
| `material_insight_explanation/material_insight_implementation_guide.md` | 권장 프로젝트 구조를 실제 폴더 구조로 반영 |
| `material_insight_explanation/docs/10-rhino-plugin-access.md` | Rhino Plugin과 백엔드 역할 분리 구조 반영 |
| `material_insight_explanation/docs/11-processing-flow-diagram.md` | Plugin, Backend, Data, Reports 영역 분리 |
| `material_insight_explanation/docs/12-implementation-phase-roadmap.md` | Phase 0 목표와 report 규칙 반영 |

설계와 구현의 일치도 측면에서, Phase 0은 다음 원칙을 만족한다.

- 실제 구현 산출물과 과제 설명 문서를 분리했다.
- FastAPI 백엔드, Mock Plugin UI, Rhino Plugin skeleton을 모두 수용할 구조를 만들었다.
- 각 phase 종료 시 report를 남기는 운영 방식을 파일 구조로 고정했다.

## 6. 남은 이슈

- 아직 실행 가능한 백엔드 코드는 없다.
- Python 패키지 설정과 FastAPI 앱은 Phase 1에서 구현해야 한다.
- 데이터 스키마는 아직 코드로 고정되지 않았다.
- PostgreSQL, OpenAI API, vLLM 설정은 아직 반영하지 않았다.
- 실제 Rhino Plugin 코드는 Phase 9에서 다룬다.

## 7. 다음 Phase 제안

다음 phase는 **Phase 1. 백엔드 Skeleton + 데이터 스키마**다.

Phase 1에서 진행할 작업:

1. Python/FastAPI 프로젝트 파일 생성
2. `/health` API 구현
3. Pydantic 모델 정의
4. 샘플 `W-012` request validation 확인
5. 기본 테스트 또는 validation script 작성

주의할 점:

- Phase 1에서는 LLM, RAG, DB 연결을 아직 붙이지 않는다.
- 먼저 API 입력과 출력 구조를 안정적으로 고정한다.
- 구현 가이드의 JSON 구조와 Pydantic schema가 정확히 맞아야 한다.
