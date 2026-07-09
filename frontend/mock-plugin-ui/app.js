const project = {
  project_id: "RHINO-PROJECT",
};

let objects = [];
let selectedObject = null;

const elements = {
  apiBaseUrl: document.querySelector("#apiBaseUrl"),
  healthButton: document.querySelector("#healthButton"),
  refreshRhinoObjectsButton: document.querySelector("#refreshRhinoObjectsButton"),
  sendSelectionButton: document.querySelector("#sendSelectionButton"),
  objectList: document.querySelector("#objectList"),
  objectDetails: document.querySelector("#objectDetails"),
  contextPreview: document.querySelector("#contextPreview"),
  selectionStatus: document.querySelector("#selectionStatus"),
  message: document.querySelector("#message"),
};

function getApiBaseUrl() {
  return elements.apiBaseUrl.value.replace(/\/$/, "");
}

function buildCpIssueContext(object) {
  if (!object) return null;
  return {
    project_id: project.project_id,
    rhino_context: {
      object_id: object.object_id,
      rhino_id: object.rhino_id,
      name: object.name,
      layer: object.layer,
      object_kind: object.object_kind,
      bbox: object.bbox || {},
      is_visible: object.is_visible,
      is_locked: object.is_locked,
    },
    intended_use: "Attach this object as optional model/location context to a CP delay issue.",
  };
}

function renderObjectList() {
  elements.objectList.innerHTML = "";
  if (!objects.length) {
    elements.objectList.innerHTML = `
      <div class="empty-state">
        Rhino 객체가 아직 동기화되지 않았습니다. Rhino에서 MaterialInsightSyncObjects를 실행한 뒤 객체 목록을 불러오세요.
      </div>
    `;
    return;
  }

  objects.forEach((object) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `object-card ${object.object_id === selectedObject?.object_id ? "active" : ""}`;
    button.innerHTML = `
      <strong>${escapeHtml(object.object_id)}</strong>
      <span>${escapeHtml(object.name || "Unnamed")} · ${escapeHtml(object.object_kind || "unknown")}</span>
      <span>${escapeHtml(object.layer || "layer missing")}</span>
    `;
    button.addEventListener("click", () => {
      selectedObject = object;
      render();
      setMessage(`CP 이슈 컨텍스트로 사용할 Rhino 객체를 선택했습니다: ${object.object_id}`);
    });
    elements.objectList.appendChild(button);
  });
}

function renderObjectDetails() {
  if (!selectedObject) {
    elements.objectDetails.innerHTML = "";
    elements.selectionStatus.textContent = "not selected";
    elements.contextPreview.textContent = "좌측 목록에서 Rhino 객체를 선택하면 CP 이슈 첨부 컨텍스트가 표시됩니다.";
    elements.sendSelectionButton.disabled = true;
    return;
  }

  elements.sendSelectionButton.disabled = false;
  elements.selectionStatus.textContent = "selected";
  const rows = [
    ["Object ID", selectedObject.object_id],
    ["Rhino ID", selectedObject.rhino_id],
    ["Name", selectedObject.name],
    ["Layer", selectedObject.layer],
    ["Geometry", selectedObject.object_kind],
    ["Visible", selectedObject.is_visible],
    ["Locked", selectedObject.is_locked],
  ];
  elements.objectDetails.innerHTML = rows
    .map(([label, value]) => `<dt>${label}</dt><dd>${formatValue(value)}</dd>`)
    .join("");
  elements.contextPreview.textContent = JSON.stringify(buildCpIssueContext(selectedObject), null, 2);
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

async function refreshRhinoObjects() {
  elements.refreshRhinoObjectsButton.disabled = true;
  setMessage("Rhino 객체 목록을 불러오는 중...");
  try {
    const result = await apiGet(`/api/v1/rhino/objects?project_id=${encodeURIComponent(project.project_id)}`);
    objects = result.objects || [];
    if (!objects.some((object) => object.object_id === selectedObject?.object_id)) {
      selectedObject = objects[0] || null;
    }
    render();
    setMessage(`Rhino 객체 ${objects.length}개를 불러왔습니다.`, "success");
  } catch (error) {
    setMessage(`Rhino 객체 목록 불러오기 실패: ${error.message}`, "error");
  } finally {
    elements.refreshRhinoObjectsButton.disabled = false;
  }
}

async function sendSelectionToRhino() {
  if (!selectedObject) {
    setMessage("먼저 좌측 목록에서 Rhino 객체를 선택하세요.", "error");
    return;
  }

  elements.sendSelectionButton.disabled = true;
  try {
    await apiPost("/api/v1/rhino/selection", {
      project_id: project.project_id,
      object_id: selectedObject.object_id,
    });
    setMessage(`선택 객체 ${selectedObject.object_id}를 Rhino로 보냈습니다. Rhino에서 MaterialInsightApplySelection을 실행하세요.`, "success");
  } catch (error) {
    setMessage(`Rhino 선택 전송 실패: ${error.message}`, "error");
  } finally {
    elements.sendSelectionButton.disabled = false;
  }
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "<span class='muted'>missing</span>";
  }
  return escapeHtml(String(value));
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function bindEvents() {
  elements.healthButton.addEventListener("click", checkHealth);
  elements.refreshRhinoObjectsButton.addEventListener("click", refreshRhinoObjects);
  elements.sendSelectionButton.addEventListener("click", sendSelectionToRhino);
}

function render() {
  renderObjectList();
  renderObjectDetails();
}

bindEvents();
render();
