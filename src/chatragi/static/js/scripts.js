/**
 * ChatRagi Script – Cleaned and Simplified
 * ----------------------------------------
 * Handles chatbot interactions, dark mode, memory/document listing,
 * toast notifications, and basic file operations.
 */

// ========== DOM Elements ==========
const chatBox = document.getElementById("chat-box");
const sendBtn = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const clearChatBtn = document.getElementById("clear-chat-btn");
const refreshBtn = document.getElementById("refresh-btn");
const markImportantBtn = document.getElementById("mark-important-btn");
const downloadBtn = document.getElementById("download-btn");
const themeToggleBtn = document.getElementById("theme-toggle-btn");
const showMemoryBtn = document.getElementById("show-memory-btn");
const memoryContainer = document.getElementById("memory-container");
const memoryBox = document.getElementById("memory-box");
const closeMemoryBtn = document.getElementById("close-memory-btn");
const showDocListBtn = document.getElementById("show-doc-list");
const sourceContainer = document.getElementById("source-container");
const sourceBox = document.getElementById("source-box");
const closeDocBtn = document.getElementById("close-doc-btn");
const toastContainer = document.querySelector(".toast-container");

let currentDocPage = 1;
let currentMemoryPage = 1;
const DOCS_PER_PAGE = 5;
const MEMORIES_PER_PAGE = 5;

// ========== Toast & Scroll ==========
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

const scrollToBottom = () => {
  chatBox.scrollTop = chatBox.scrollHeight;
};

// ========== Chatbot ==========
async function sendMessage() {
  const query = userInput.value.trim();
  if (!query) return;

  // Show user message
  const userBubble = document.createElement("div");
  userBubble.className = "user-message";
  userBubble.innerHTML = `
    <div class="message-label">You:</div>
    <div class="message-content">${query}</div>`;
  chatBox.appendChild(userBubble);
  userInput.value = "";
  scrollToBottom();

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    const data = await res.json();

    // Error bubble
    if (data.error) {
      const errorBubble = document.createElement("div");
      errorBubble.className = "ai-message";
      errorBubble.innerHTML = `
        <div class="message-label">Error:</div>
        <div class="message-content">${data.error}</div>`;
      chatBox.appendChild(errorBubble);
    } else {
      // AI response
      const aiBubble = document.createElement("div");
      aiBubble.className = "ai-message";
      aiBubble.innerHTML = `
        <div class="message-label">ChatRagi:</div>
        <div class="message-content">${marked.parse(data.answer)}</div>`;
      chatBox.appendChild(aiBubble);

      const separator = document.createElement("hr");
      chatBox.appendChild(separator);
    }

    scrollToBottom();
  } catch {
    const errorBubble = document.createElement("div");
    errorBubble.className = "ai-message";
    errorBubble.innerHTML = `
      <div class="message-label">Error:</div>
      <div class="message-content">Server unreachable.</div>`;
    chatBox.appendChild(errorBubble);
    scrollToBottom();
  }
}

// ========== Memory Handling ==========
const savedConversations = new Set();

async function storeMemory(markImportant = false) {
  const lastUser = [...document.querySelectorAll(".user-message")].at(-1);
  const lastAI = [...document.querySelectorAll(".ai-message")].at(-1);
  if (!lastUser || !lastAI) {
    showToast("No conversation to mark.", "error");
    return;
  }

  const user_query = lastUser.innerText.replace("You:", "").trim();
  const response = lastAI.innerText.replace("ChatRagi:", "").trim();
  const key = `${user_query}|||${response}`;

  if (markImportant && savedConversations.has(key)) {
    showToast("This conversation is already marked as important.", "error");
    return;
  }

  try {
    const res = await fetch("/store-memory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_query, response, is_important: markImportant })
    });
    const result = await res.json();

    if (result.status === "success") {
      if (markImportant) savedConversations.add(key);
      showToast("Conversation marked as important.");
    } else {
      showToast("Failed to mark important.", "error");
    }
  } catch {
    showToast("Error storing memory.", "error");
  }
}

// ========== Pagination Renderer ==========
function renderPaginatedCards(container, items, page, itemsPerPage, type, paginationHandler, idPrefix = "") {
  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const paginatedItems = items.slice(start, end);
  const totalPages = Math.ceil(items.length / itemsPerPage);

  container.innerHTML = "";

  const pagination = document.createElement("div");
  pagination.className = "pagination-controls";
  pagination.innerHTML = `
    <button id="${idPrefix}-prev-btn" ${page === 1 ? "disabled" : ""}>&laquo; Prev</button>
    <span>Page ${page} of ${totalPages}</span>
    <button id="${idPrefix}-next-btn" ${end >= items.length ? "disabled" : ""}>Next &raquo;</button>`;
  container.appendChild(pagination);

  document.getElementById(`${idPrefix}-prev-btn`)?.addEventListener("click", () => paginationHandler(page - 1));
  document.getElementById(`${idPrefix}-next-btn`)?.addEventListener("click", () => paginationHandler(page + 1));

  paginatedItems.forEach(entry => {
    const card = document.createElement("div");
    card.className = type === "memory" ? "memory-card" : "document-card";

    const headerClass = type === "memory" ? "mem-header" : "doc-header";
    const titleClass = type === "memory" ? "mem-title" : "doc-title";
    const detailsClass = type === "memory" ? "mem-details" : "doc-details";
    const metaClass = type === "memory" ? "mem-meta" : "doc-meta";

    const title = type === "memory" ? entry.user_query : entry.file_name;
    const caret = `<span class="caret-icon">▶</span>`;
    const header = `<div class="${headerClass}">${caret}<span class="${titleClass}">${title}</span></div>`;

    const details = type === "memory"
      ? `
        <div class="${detailsClass}">
          <div class="${metaClass}"><strong>Timestamp:</strong> ${new Date(entry.timestamp).toLocaleString()}</div>
          <div class="${metaClass}"><strong>Answer:</strong> ${entry.conversation}</div>
          <div class="${metaClass}"><strong>Important:</strong> ${entry.important ? "Yes" : "No"}</div>
        </div>`
      : `
        <div class="${detailsClass}">
          <div class="${metaClass}"><strong>Type:</strong> ${entry.source}</div>
          <div class="${metaClass}"><strong>Chunks:</strong> ${entry.chunks ?? 0}</div>
        </div>`;

    card.innerHTML = header + details;
    container.appendChild(card);
  });

  container.querySelectorAll(`.${type === "memory" ? "mem-header" : "doc-header"}`).forEach(header => {
    header.addEventListener("click", () => {
      const details = header.nextElementSibling;
      const caret = header.querySelector(".caret-icon");
      details.classList.toggle("visible");
      caret.textContent = details.classList.contains("visible") ? "▼" : "▶";
    });
  });
}

// ========== View Handlers ==========
async function showMemory() {
  memoryContainer.classList.add("active");
  sourceContainer.classList.remove("active");
  memoryBox.innerHTML = "<p>Loading...</p>";

  try {
    const res = await fetch("/all-memories");
    const data = await res.json();
    if (!data.memories || data.memories.length === 0) {
      memoryBox.innerHTML = "<p>No memory found.</p>";
      return;
    }
    renderPaginatedCards(memoryBox, data.memories, currentMemoryPage, MEMORIES_PER_PAGE, "memory",
      newPage => { currentMemoryPage = newPage; showMemory(); },
      "mem"
    );
  } catch {
    memoryBox.innerHTML = "<p>Error loading memories.</p>";
  }
}

async function showDocs() {
  memoryContainer.classList.remove("active");
  sourceContainer.classList.add("active");
  sourceBox.innerHTML = "<p>Loading...</p>";

  try {
    const res = await fetch("/list-documents");
    const data = await res.json();
    if (!data.documents || data.documents.length === 0) {
      sourceBox.innerHTML = "<p>No documents found.</p>";
      return;
    }
    renderPaginatedCards(sourceBox, data.documents, currentDocPage, DOCS_PER_PAGE, "document",
      newPage => { currentDocPage = newPage; showDocs(); },
      "doc"
    );
  } catch (e) {
    sourceBox.innerHTML = `<p>Error loading documents: ${e.message}</p>`;
  }
}

// ========== Utilities ==========
function downloadChat() {
  const text = chatBox.innerText.trim();
  if (!text) {
    showToast("Chat is empty. Nothing to download.", "error");
    return;
  }

  const blob = new Blob([text], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "chatragi_session.txt";
  a.click();
}

async function refreshIndex() {
  const res = await fetch("/refresh", { method: "POST" });
  const data = await res.json();
  showToast(data.response);
}

function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
  showToast("Theme toggled.");
}

// ========== Event Listeners ==========
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => e.key === "Enter" && sendMessage());
clearChatBtn.addEventListener("click", () => (chatBox.innerHTML = ""));
refreshBtn.addEventListener("click", refreshIndex);
markImportantBtn.addEventListener("click", () => storeMemory(true));
downloadBtn.addEventListener("click", downloadChat);
themeToggleBtn.addEventListener("click", toggleDarkMode);
showMemoryBtn.addEventListener("click", showMemory);
showDocListBtn.addEventListener("click", showDocs);
closeMemoryBtn.addEventListener("click", () => memoryContainer.classList.remove("active"));
closeDocBtn.addEventListener("click", () => sourceContainer.classList.remove("active"));