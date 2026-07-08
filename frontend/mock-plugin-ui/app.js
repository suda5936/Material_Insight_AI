const project = {
  project_id: "PRJ-MOCK-001",
  project_type: "interior",
  design_stage: "basic_design",
  building_use: "office",
  region: "KR",
  priority: "performance",
};

const sampleObjects = [
  {
    object_id: "W-012",
    object_type: "interior_wall",
    layer: "A-WALL",
    name: "MeetingRoom_Wall_012",
    space_type: "meeting_room",
    material: null,
    thickness_mm: 75,
    review_status: "pending",
    geometry: { object_kind: "Brep", area_m2: 12.4, bbox: {} },
    user_attributes: { fire_rating: null, acoustic_required: true },
  },
  {
    object_id: "F-021",
    object_type: "floor_finish",
    layer: "A-FLOR",
    name: "Office_Floor_021",
    space_type: "office",
    material: "vinyl tile",
    thickness_mm: 5,
    review_status: "reviewed",
    geometry: { object_kind: "Brep", area_m2: 32.0, bbox: {} },
    user_attributes: { wet_area: false },
  },
  {
    object_id: "F-020",
    object_type: "floor_finish",
    layer: "A-FLOR",
    name: "Restroom_Floor_020",
    space_type: "restroom",
    material: "carpet tile",
    thickness_mm: 8,
    review_status: "pending",
    geometry: { object_kind: "Brep", area_m2: 9.5, bbox: {} },
    user_attributes: { wet_area: true },
  },
  {
    object_id: "S-040",
    object_type: "slab",
    layer: "S-SLAB",
    name: "Structural_Slab_040",
    space_type: "office",
    material: "reinforced concrete",
    thickness_mm: 180,
    review_status: "pending",
    geometry: { object_kind: "Brep", area_m2: 48.1, volume_m3: 8.6, bbox: {} },
    user_attributes: { structural_role: "load_bearing" },
  },
  {
    object_id: "OBJ-UNKNOWN",
    object_type: null,
    layer: "DEFAULT",
    name: "Unnamed_Object",
    space_type: null,
    material: null,
    thickness_mm: null,
    review_status: "pending",
    geometry: { object_kind: "Brep", bbox: {} },
    user_attributes: {},
  },
];

let selectedObject = sampleObjects[0];
let latestRecommendation = null;

const elements = {
  apiBaseUrl: document.querySelector("#apiBaseUrl"),
  healthButton: document.querySelector("#healthButton"),
  objectList: document.querySelector("#objectList"),
  objectDetails: document.querySelector("#objectDetails"),
  payloadPreview: document.querySelector("#payloadPreview"),
  reviewButton: document.querySelector("#reviewButton"),
  loadRhinoReviewButton: document.querySelector("#loadRhinoReviewButton"),
  recommendation: document.querySelector("#recommendation"),
  message: document.querySelector("#message"),
  resultSeverity: document.querySelector("#resultSeverity"),
  reviewStatus: document.querySelector("#reviewStatus"),
  editReason: document.querySelector("#editReason"),
  scanButton: document.querySelector("#scanButton"),
  scanSummary: document.querySelector("#scanSummary"),
  scanResults: document.querySelector("#scanResults"),
  actionButtons: document.querySelectorAll("[data-action]"),
};

function getApiBaseUrl() {
  return elements.apiBaseUrl.value.replace(/\/$/, "");
}

function buildReviewPayload(object) {
  return { project, object };
}

function renderObjectList() {
  elements.objectList.innerHTML = "";
  sampleObjects.forEach((object) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `object-card ${object.object_id === selectedObject.object_id ? "active" : ""}`;
    button.innerHTML = `
      <strong>${object.object_id}</strong>
      <span>${object.name || "Unnamed"} · ${object.object_type || "unknown"}</span>
      <span>${object.space_type || "space missing"} · ${object.material || "material missing"}</span>
    `;
    button.addEventListener("click", () => {
      selectedObject = object;
      latestRecommendation = null;
      render();
    });
    elements.objectList.appendChild(button);
  });
}

function renderObjectDetails() {
  const rows = [
    ["Object ID", selectedObject.object_id],
    ["Name", selectedObject.name],
    ["Type", selectedObject.object_type],
    ["Layer", selectedObject.layer],
    ["Space", selectedObject.space_type],
    ["Material", selectedObject.material],
    ["Thickness", selectedObject.thickness_mm ? `${selectedObject.thickness_mm} mm` : null],
    ["Geometry", selectedObject.geometry?.object_kind],
  ];
  elements.objectDetails.innerHTML = rows
    .map(([label, value]) => `<dt>${label}</dt><dd>${value ?? "<span class='muted'>missing</span>"}</dd>`)
    .join("");
  elements.reviewStatus.textContent = selectedObject.review_status || "pending";
  elements.payloadPreview.textContent = JSON.stringify(buildReviewPayload(selectedObject), null, 2);
}

function renderRecommendation() {
  if (!latestRecommendation) {
    elements.recommendation.className = "recommendation empty-state";
    elements.recommendation.textContent = "아직 검토 결과가 없습니다.";
    elements.resultSeverity.textContent = "not run";
    elements.resultSeverity.className = "status-pill neutral";
    return;
  }

  elements.recommendation.className = "recommendation";
  elements.resultSeverity.textContent = latestRecommendation.severity;
  elements.resultSeverity.className = `status-pill ${latestRecommendation.severity}`;
  const sections = [
    ["요약", [latestRecommendation.summary]],
    ["탐지된 문제", latestRecommendation.detected_issues],
    ["재료 후보", latestRecommendation.material_candidates],
    ["성능 메모", latestRecommendation.performance_notes],
    ["주의사항", latestRecommendation.disclaimers],
  ];
  const sourceItems = latestRecommendation.sources.map(
    (source) => `${source.document_id} · ${source.title} · score ${source.score}`,
  );
  elements.recommendation.innerHTML = [
    ...sections.map(([title, items]) => renderResultSection(title, items)),
    renderResultSection("근거 문서", sourceItems.length ? sourceItems : ["관련 근거 없음"]),
    renderThicknessGuidance(),
  ].join("");
}

function renderResultSection(title, items) {
  const safeItems = items && items.length ? items : ["없음"];
  return `
    <div class="result-section">
      <h3>${title}</h3>
      <ul>${safeItems.map((item) => `<li>${String(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function renderThicknessGuidance() {
  const guidance = latestRecommendation.thickness_guidance || {};
  const items = Object.keys(guidance).map((key) => `${key}: ${guidance[key]}`);
  return renderResultSection("두께 검토", items.length ? items : ["별도 안내 없음"]);
}

function setMessage(text, type = "") {
  elements.message.textContent = text;
  elements.message.className = `message ${type}`.trim();
}

async function apiPost(path, body) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${text}`);
  }
  return response.json();
}

async function apiGet(path) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${text}`);
  }
  return response.json();
}

async function checkHealth() {
  try {
    const response = await fetch(`${getApiBaseUrl()}/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    setMessage("Backend 연결이 정상입니다.", "success");
  } catch (error) {
    setMessage(`Backend 연결 실패: ${error.message}`, "error");
  }
}

async function reviewSelectedObject() {
  elements.reviewButton.disabled = true;
  setMessage(`${selectedObject.object_id} 검토 중...`);
  try {
    latestRecommendation = await apiPost("/api/v1/review-object", buildReviewPayload(selectedObject));
    setMessage("AI 검토 결과를 받았습니다.", "success");
    renderRecommendation();
  } catch (error) {
    setMessage(`AI 검토 실패: ${error.message}`, "error");
  } finally {
    elements.reviewButton.disabled = false;
  }
}

async function loadLatestRhinoReview({ quiet = false } = {}) {
  if (!quiet) {
    setMessage("Rhino 최신 검토 결과를 불러오는 중...");
  }
  try {
    const result = await apiGet("/api/v1/latest-review");
    if (!result) {
      if (!quiet) setMessage("아직 Rhino에서 전달된 검토 결과가 없습니다.");
      return;
    }
    if (latestRecommendation?.recommendation_id === result.recommendation_id) {
      if (!quiet) setMessage("이미 최신 Rhino 검토 결과가 표시되어 있습니다.", "success");
      return;
    }
    latestRecommendation = result;
    setMessage(`Rhino 객체 ${result.object_id}의 검토 결과를 표시합니다.`, "success");
    renderRecommendation();
  } catch (error) {
    if (!quiet) setMessage(`Rhino 결과 불러오기 실패: ${error.message}`, "error");
  }
}

async function submitAction(action) {
  if (!latestRecommendation) {
    setMessage("먼저 AI 검토를 실행하세요.", "error");
    return;
  }
  const editedValues =
    action === "edit"
      ? {
          review_status: "reviewed",
          note: elements.editReason.value,
        }
      : {};
  try {
    const result = await apiPost("/api/v1/review-actions", {
      recommendation_id: latestRecommendation.recommendation_id,
      object_id: selectedObject.object_id,
      user_id: "demo_designer",
      action,
      edited_values: editedValues,
      sources: latestRecommendation.sources,
      reason: elements.editReason.value || null,
    });
    setMessage(`사용자 액션 저장 완료: ${result.review_action_id}`, "success");
  } catch (error) {
    setMessage(`액션 저장 실패: ${error.message}`, "error");
  }
}

async function scanModel() {
  elements.scanButton.disabled = true;
  elements.scanResults.textContent = "전체 모델 검사 중...";
  elements.scanResults.className = "scan-results empty-state";
  try {
    const result = await apiPost("/api/v1/scan-model", {
      project,
      objects: sampleObjects,
    });
    renderScanResults(result);
    setMessage("전체 모델 QA 결과를 받았습니다.", "success");
  } catch (error) {
    elements.scanResults.textContent = `전체 검사 실패: ${error.message}`;
    setMessage(`전체 검사 실패: ${error.message}`, "error");
  } finally {
    elements.scanButton.disabled = false;
  }
}

function renderScanResults(result) {
  elements.scanSummary.textContent = `${result.summary.objects_with_issues}/${result.summary.total_objects} issue`;
  elements.scanSummary.className = "status-pill neutral";
  if (!result.results.length) {
    elements.scanResults.className = "scan-results empty-state";
    elements.scanResults.textContent = "검토 이슈가 없습니다.";
    return;
  }
  elements.scanResults.className = "scan-results";
  elements.scanResults.innerHTML = result.results
    .map(
      (row) => `
        <div class="scan-row">
          <strong>${row.object_id}</strong>
          <span>${row.issues.map((issue) => issue.issue_code).join(", ") || "no issues"}</span>
          <span class="status-pill ${row.severity}">${row.required_action}</span>
        </div>
      `,
    )
    .join("");
}

function bindEvents() {
  elements.healthButton.addEventListener("click", checkHealth);
  elements.reviewButton.addEventListener("click", reviewSelectedObject);
  elements.loadRhinoReviewButton.addEventListener("click", () => loadLatestRhinoReview());
  elements.scanButton.addEventListener("click", scanModel);
  elements.actionButtons.forEach((button) => {
    button.addEventListener("click", () => submitAction(button.dataset.action));
  });
}

function render() {
  renderObjectList();
  renderObjectDetails();
  renderRecommendation();
}

bindEvents();
render();
window.setInterval(() => loadLatestRhinoReview({ quiet: true }), 4000);
