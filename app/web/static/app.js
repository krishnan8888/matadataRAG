const health = document.querySelector("#health");
const fileInput = document.querySelector("#file-input");
const dropZone = document.querySelector("#drop-zone");
const uploadList = document.querySelector("#upload-list");
const documentList = document.querySelector("#document-list");
const refreshDocuments = document.querySelector("#refresh-documents");
const queryForm = document.querySelector("#query-form");
const queryInput = document.querySelector("#query-input");
const askButton = document.querySelector("#ask-button");
const answerState = document.querySelector("#answer-state");
const answerSection = document.querySelector("#answer-section");
const answerText = document.querySelector("#answer-text");
const evidenceSection = document.querySelector("#evidence-section");
const chosenDocuments = document.querySelector("#chosen-documents");
const evidenceList = document.querySelector("#evidence-list");
const toggleEvidence = document.querySelector("#toggle-evidence");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }

  return payload;
}

function setHealth(online, label) {
  health.classList.toggle("online", online);
  health.classList.toggle("offline", !online);
  health.querySelector("span:last-child").textContent = label;
}

async function checkHealth() {
  try {
    const payload = await api("/api/health");
    setHealth(true, `${payload.documents} documents ready`);
  } catch {
    setHealth(false, "Backend unavailable");
  }
}

function renderDocuments(documents) {
  if (!documents.length) {
    documentList.innerHTML = '<div class="document-item"><p>No ingested documents yet.</p></div>';
    return;
  }

  documentList.innerHTML = documents.map((document) => {
    const modes = (document.retrieval_modes || [])
      .map((mode) => `<span class="tag">${escapeHtml(mode)}</span>`)
      .join("");

    return `
      <article class="document-item">
        <strong>${escapeHtml(document.document_id)}</strong>
        <p>${escapeHtml(document.document_type || "Unknown type")} · ${escapeHtml(document.embedding_mode || "No embedding mode")}</p>
        <div class="tag-row">${modes}</div>
      </article>
    `;
  }).join("");
}

async function loadDocuments() {
  documentList.innerHTML = '<div class="document-item"><p>Loading documents...</p></div>';

  try {
    const payload = await api("/api/documents");
    renderDocuments(payload.documents);
    await checkHealth();
  } catch (error) {
    documentList.innerHTML = `<div class="document-item"><p>${escapeHtml(error.message)}</p></div>`;
  }
}

function addUploadItem(filename) {
  const item = document.createElement("div");
  item.className = "upload-item";
  item.innerHTML = `<span>${escapeHtml(filename)}</span><span>Queued</span>`;
  uploadList.prepend(item);
  return item;
}

async function uploadFiles(files) {
  for (const file of files) {
    const item = addUploadItem(file.name);
    const status = item.querySelector("span:last-child");
    status.textContent = "Ingesting";

    const form = new FormData();
    form.append("file", file);

    try {
      const result = await api("/api/ingest", {
        method: "POST",
        body: form,
      });
      status.textContent = `Ready · ${result.metadata.embedding_mode}`;
      status.className = "success";
    } catch (error) {
      status.textContent = error.message;
      status.className = "error";
    }
  }

  fileInput.value = "";
  await loadDocuments();
}

function renderQueryResult(payload) {
  answerState.classList.add("hidden");
  answerSection.classList.remove("hidden");
  evidenceSection.classList.remove("hidden");
  answerText.textContent = payload.answer;

  chosenDocuments.innerHTML = payload.chosen_documents.length
    ? payload.chosen_documents.map((document) => `
        <span class="chosen-document">
          ${escapeHtml(document.document_id)} · score ${Number(document.metadata_score || 0).toFixed(1)}
        </span>
      `).join("")
    : '<span class="chosen-document">No documents selected</span>';

  evidenceList.innerHTML = payload.results.length
    ? payload.results.map((result) => `
        <article class="evidence-item">
          <header>
            <strong>${escapeHtml(result.document_id)}</strong>
            <span>${escapeHtml(result.source)} · score ${Number(result.score || 0).toFixed(3)}</span>
          </header>
          <p>${escapeHtml(result.content)}</p>
        </article>
      `).join("")
    : '<article class="evidence-item"><p>No evidence retrieved.</p></article>';
}

queryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();

  if (!query) return;

  askButton.disabled = true;
  askButton.textContent = "Working";
  answerSection.classList.add("hidden");
  evidenceSection.classList.add("hidden");
  answerState.className = "answer-state loading";
  answerState.innerHTML = "<p>Retrieving evidence and generating a grounded answer...</p>";

  try {
    const payload = await api("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    renderQueryResult(payload);
  } catch (error) {
    answerState.className = "answer-state error";
    answerState.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Ask";
  }
});

toggleEvidence.addEventListener("click", () => {
  const hidden = evidenceList.classList.toggle("hidden");
  chosenDocuments.classList.toggle("hidden", hidden);
  toggleEvidence.textContent = hidden ? "Show evidence" : "Hide evidence";
});

fileInput.addEventListener("change", () => uploadFiles(fileInput.files));
refreshDocuments.addEventListener("click", loadDocuments);

for (const eventName of ["dragenter", "dragover"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
}

dropZone.addEventListener("drop", (event) => {
  uploadFiles(event.dataTransfer.files);
});

checkHealth();
loadDocuments();
