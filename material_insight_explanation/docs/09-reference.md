# 9. 기대 효과, 한계 및 참고문헌

## 9.1 기대 효과

Material Insight AI는 설계자의 판단을 자동화하기보다, 반복적인 정보 확인과 1차 검토를 지원하는 데 목적이 있다.

### 업무 효율 향상

- 객체별 재료와 두께 검토 시간 단축
- 시방서와 카탈로그 검색 시간 감소
- 누락 객체를 전체 모델에서 빠르게 탐지
- 반복적인 검토 요청 작성 자동화

### 설계 품질 향상

- 객체 속성 누락 조기 발견
- 유사 객체 간 정보 일관성 향상
- 추천 근거와 문서 출처 제공
- 초급 설계자의 검토 항목 이해 지원

### 협업과 지식 관리 개선

- 객체별 검토 상태와 변경 이유 기록
- 시니어 설계자와 전문가에게 구조화된 검토 요청 전달
- 사내 설계 기준과 과거 사례 재사용
- 개인 경험을 조직 지식으로 전환

---

## 9.2 예상되는 한계

### 1. 입력 데이터 품질 의존

레이어, 객체명, 재료와 공간 용도가 불명확하면 Agent도 정확한 판단을 수행하기 어렵다. 따라서 객체 분류 규칙과 필수 속성 체계가 필요하다.

### 2. 프로젝트별 차이

같은 객체 유형이라도 건물 용도, 지역, 고객 요구와 구조 방식에 따라 적절한 구성이 달라질 수 있다. 일반적인 추천을 모든 프로젝트에 그대로 적용해서는 안 된다.

### 3. 구조 및 법규 판단의 제한

구조 안전성과 법규 적합성은 전체 프로젝트 조건과 최신 기준을 종합적으로 검토해야 한다. Agent는 관련 근거와 검토 필요성을 제공하되 최종 판단을 수행하지 않는다.

### 4. 문서 최신성 문제

RAG에 오래된 시방서나 카탈로그가 등록되면 잘못된 근거가 검색될 수 있다. 문서 버전, 유효기간과 승인 상태를 지속적으로 관리해야 한다.

### 5. 초기 구축 비용

플러그인 개발뿐 아니라 객체 분류체계, 규칙, 문서 메타데이터와 승인 프로세스를 함께 설계해야 한다. 기업 적용 시 기술 개발보다 데이터 정비에 더 많은 노력이 필요할 수 있다.

---

## 9.3 향후 확장 방향

MVP 검증 이후 다음 단계로 확장할 수 있다.

1. AutoCAD와 Revit 연동
2. IFC 기반 객체 유형과 속성 매핑
3. 구조·법규 전문가 검토 워크플로우 연동
4. 재료표와 검토 보고서 자동 생성
5. 제조사 제품 정보와 단가 API 연동
6. 프로젝트 전체 QA 대시보드
7. 사내 LLM 또는 전용 클라우드 배포
8. 다중 사용자 승인과 권한 관리

---

## 9.4 결론

본 프로젝트는 건축·공간 설계 업무에서 반복적으로 발생하는 재료 정보 누락, 부재 두께 검토, 시방서 검색과 변경 이력 관리 문제를 해결하기 위해 **Rhino/CAD 플러그인형 AI Agent**를 제안하였다.

현재 건축 분야의 AI는 초기 설계 대안 생성, 대지 분석, 시각화와 BIM 검토에 활발히 적용되고 있다. 그러나 자유형 CAD/Rhino 객체와 기술 문서를 연결해 재료·두께·성능 검토를 지원하는 영역은 상대적으로 부족하다.

Material Insight AI는 다음 요소를 결합한다.

- Rhino 객체 메타데이터 추출
- Rule Engine 기반 누락과 범위 검사
- RAG 기반 시방서와 카탈로그 검색
- LLM 기반 설명형 추천
- 설계자와 전문가의 최종 승인
- 검토 결과와 변경 이력 저장

이 구조의 핵심은 AI가 설계자를 대체하지 않는다는 점이다. AI는 반복적인 정보 탐색과 1차 검토를 수행하고, 설계자는 프로젝트 맥락과 전문성을 바탕으로 최종 판단을 내린다.

따라서 Material Insight AI는 제한된 범위의 MVP로 구현 가능하면서도, 향후 BIM, 기업 지식 관리와 협업 시스템으로 확장할 수 있는 현실적인 AI Agent 도입 전략이다.

---

## 9.5 참고문헌 및 공식 자료

### Rhino 및 플러그인 개발

1. Robert McNeel & Associates, **Your First Plugin (Windows)**, Rhino Developer Documentation.  
   <https://developer.rhino3d.com/guides/rhinocommon/your-first-plugin-windows/>

2. Robert McNeel & Associates, **Rhino.DocObjects.ObjectAttributes Class**, RhinoCommon API Documentation.  
   <https://developer.rhino3d.com/api/rhinocommon/rhino.docobjects.objectattributes>

### BIM 및 데이터 표준

3. buildingSMART International, **Industry Foundation Classes (IFC)**.  
   <https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/>

4. Autodesk, **What Is BIM?**  
   <https://www.autodesk.com/solutions/aec/bim>

### 건축·설계 AI 사례

5. Autodesk, **Forma Site Design Overview**.  
   <https://www.autodesk.com/products/forma/overview>

6. TestFit, **Real Estate Feasibility Platform**.  
   <https://www.testfit.io/>

7. EvolveLAB, **Veras AI Visualization**.  
   <https://www.evolvelab.io/veras>

### 기술 및 구현 자료

8. FastAPI, **FastAPI Documentation**.  
   <https://fastapi.tiangolo.com/>

9. PostgreSQL, **PostgreSQL Documentation**.  
   <https://www.postgresql.org/docs/>

10. pgvector, **Open-source Vector Similarity Search for PostgreSQL**.  
    <https://github.com/pgvector/pgvector>

---

## 9.6 제출 전 참고문헌 보완 사항

최종 제출 전에는 다음 자료를 추가하는 것이 좋다.

- 국내 건축법과 관련 시행령
- 국토교통부 고시 및 건축 기준
- KS 재료·차음·내화 관련 표준
- 실제 제조사 자재 카탈로그
- 과거 설계 프로젝트 사례
- 수업에서 제공된 AI Agent 및 RAG 자료

법규와 표준은 반드시 최신 공식 원문을 확인하고, 보고서에는 문서명, 발행기관, 개정일과 접근일을 함께 기록한다.

---

## 9.7 최종 보고서 구성

최종 보고서는 다음 Markdown 문서를 순서대로 결합해 구성한다.

```text
README.md
docs/
├── 01-background.md
├── 02-industry-analysis.md
├── 03-ai-landscape.md
├── 04-agent-candidates.md
├── 05-mvp-design.md
├── 06-architecture.md
├── 07-rag-hitl.md
├── 08-demo.md
└── 09-reference.md
```

각 문서를 하나의 보고서로 결합한 뒤 표지, 목차, 페이지 번호와 참고문헌 형식을 최종 정리한다.
