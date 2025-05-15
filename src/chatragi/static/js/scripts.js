/**
 * ChatRagi Scripts
 * ----------------------------------------
 * Handles chatbot interactions, dark mode, memory/document browsing,
 * toast notifications, and chat session downloads.
 */

// ======= DOM Elements =======
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const clearChatBtn = document.getElementById("clear-chat-btn");
const refreshBtn = document.getElementById("refresh-btn");
const markImportantBtn = document.getElementById("mark-important-btn");
const downloadBtn = document.getElementById("download-btn");
const themeToggleBtn = document.getElementById("theme-toggle-btn");
const showMemoryBtn = document.getElementById("show-memory-btn");
const showDocListBtn = document.getElementById("show-doc-list");
const memoryContainer = document.getElementById("memory-container");
const memoryBox = document.getElementById("memory-box");
const closeMemoryBtn = document.getElementById("close-memory-btn");
const sourceContainer = document.getElementById("source-container");
const sourceBox = document.getElementById("source-box");
const closeDocBtn = document.getElementById("close-doc-btn");
const toastContainer = document.querySelector(".toast-container");

// ======= Pagination State =======
let currentDocPage = 1;
let currentMemoryPage = 1;
const DOCS_PER_PAGE = 5;
const MEMORIES_PER_PAGE = 5;

// ======= In-memory Cache =======
const chatMemoryCache = new Map();
const savedConversations = new Set();

// ======= Toast Notifications =======
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ======= Scroll =======
function scrollToBottom(force = false) {
  const distanceFromBottom = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;
  if (force || distanceFromBottom < 200) {
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
  }
}

// ======= Message Creation =======
function createMessageBubble(label, content, className) {
  const bubble = document.createElement("div");
  bubble.className = className;
  bubble.innerHTML = `
    <div class="message-label">${label}</div>
    <div class="message-content">${content}</div>`;
  return bubble;
}

// ======= Sending Message (Updated for Persona) =======
async function sendMessage() {
  const query = userInput.value.trim();
  if (!query) return;

  chatBox.appendChild(createMessageBubble("You:", query, "user-message"));
  userInput.value = "";
  scrollToBottom();

  // Capture selected persona (default if not found)
  const personaSelect = document.getElementById("persona-select");
  const persona = personaSelect ? personaSelect.value : "default";

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, persona })  // Send persona with query
    });
    const data = await res.json();

    if (data.error) {
      chatBox.appendChild(createMessageBubble("Error:", data.error, "ai-message"));
      scrollToBottom();
      return;
    }

    const formattedAnswer = data.answer || "";
    const rawAnswer = data.raw_answer || "";
    const citations = data.citations || [];

    const aiBubble = document.createElement("div");
    aiBubble.className = "ai-message";
    aiBubble.innerHTML = `
      <div class="message-label">ChatRagi:</div>
      <div class="message-content">${marked.parse(formattedAnswer)}</div>`;
    chatBox.appendChild(aiBubble);

    if (citations.length > 0) {
      const citationSection = document.createElement("div");
      citationSection.className = "citation-section";
      citationSection.innerHTML = `<strong>Sources:</strong><ul>${citations.map(c => `<li>${c}</li>`).join("")}</ul>`;
      chatBox.appendChild(citationSection);
    }

    chatBox.appendChild(document.createElement("hr"));
    chatMemoryCache.set("latest", { user_query: query, response: rawAnswer });

    scrollToBottom(true);
  } catch (err) {
    chatBox.appendChild(createMessageBubble("Error:", "Server unreachable.", "ai-message"));
    console.error("Error sending message:", err);
    scrollToBottom(true);
  }
}

// ======= Store Memory =======
async function storeMemory(markImportant = false) {
  const memory = chatMemoryCache.get("latest");
  if (!memory) {
    showToast("No conversation to save.", "error");
    return;
  }

  const { user_query, response } = memory;
  const key = `${user_query}|||${response}`;

  if (markImportant && savedConversations.has(key)) {
    showToast("Already marked as important.", "info");
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
      showToast(markImportant ? "Marked as important." : "Memory saved successfully.");
      scrollToBottom();
    } else {
      showToast("Failed to store memory.", "error");
    }
  } catch (err) {
    console.error("Error storing memory:", err);
    showToast("Error storing memory.", "error");
  }
}

// ======= Pagination Renderer =======
function renderPaginatedCards(container, items, page, itemsPerPage, type, paginationHandler, idPrefix = "") {
  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
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

  paginatedItems = items.slice(start, end);
  paginatedItems.forEach(entry => {
    const card = document.createElement("div");
    card.className = type === "memory" ? "memory-card" : "document-card";

    const headerClass = type === "memory" ? "mem-header" : "doc-header";
    const titleClass = type === "memory" ? "mem-title" : "doc-title";
    const detailsClass = type === "memory" ? "mem-details" : "doc-details";
    const metaClass = type === "memory" ? "mem-meta" : "doc-meta";

    const title = type === "memory" ? entry.user_query : entry.file_name;
    const header = `<div class="${headerClass}"><span class="caret-icon">▶</span><span class="${titleClass}">${title}</span></div>`;

    const details = type === "memory"
      ? `<div class="${detailsClass}">
          <div class="${metaClass}"><strong>Timestamp:</strong> ${new Date(entry.timestamp).toLocaleString()}</div>
          <div class="${metaClass}"><strong>Answer:</strong> ${entry.conversation}</div>
          <div class="${metaClass}"><strong>Important:</strong> ${entry.important ? "Yes" : "No"}</div>
        </div>`
      : `<div class="${detailsClass}">
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
  
      if (details.classList.contains("visible")) {
        caret.style.transform = "rotate(90deg)";  // Rotate right when open
      } else {
        caret.style.transform = "rotate(0deg)";    // Point right when closed
      }
    });
  });
}

// ======= Memory & Documents =======
async function showMemory() {
  showToast("Loading saved memory...");
  memoryContainer.classList.add("active");
  sourceContainer.classList.remove("active");
  memoryBox.innerHTML = "<p>Loading...</p>";

  try {
    const res = await fetch("/all-memories");
    const data = await res.json();
    if (!data.memories?.length) {
      memoryBox.innerHTML = "<p>No memory found.</p>";
      return;
    }
    renderPaginatedCards(memoryBox, data.memories, currentMemoryPage, MEMORIES_PER_PAGE, "memory", page => { currentMemoryPage = page; showMemory(); }, "mem");
  } catch (e) {
    memoryBox.innerHTML = "<p>Error loading memories.</p>";
  }
}

async function showDocs() {
  showToast("Loading source documents...");
  memoryContainer.classList.remove("active");
  sourceContainer.classList.add("active");
  sourceBox.innerHTML = "<p>Loading...</p>";

  try {
    const res = await fetch("/list-documents");
    const data = await res.json();
    if (!data.documents?.length) {
      sourceBox.innerHTML = "<p>No documents found.</p>";
      return;
    }
    renderPaginatedCards(sourceBox, data.documents, currentDocPage, DOCS_PER_PAGE, "document", page => { currentDocPage = page; showDocs(); }, "doc");
  } catch (e) {
    sourceBox.innerHTML = `<p>Error loading documents: ${e.message}</p>`;
  }
}

// ======= Miscellaneous Actions =======
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
  showToast(data.response || "Index refreshed.");
}

function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
  showToast("Theme toggled.");
}

function clearChat() {
  chatBox.innerHTML = "";
  userInput.value = "";
  chatMemoryCache.delete("latest");
  showToast("Chat cleared.", "info");
}

// ======= Button Bindings =======
document.addEventListener("DOMContentLoaded", () => {
  userInput.focus();
  userInput.scrollIntoView({ behavior: "smooth", block: "end" });
  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", e => e.key === "Enter" && sendMessage());
  markImportantBtn.addEventListener("click", () => storeMemory(true));
  clearChatBtn.addEventListener("click", clearChat);
  downloadBtn.addEventListener("click", downloadChat);
  refreshBtn.addEventListener("click", refreshIndex);
  themeToggleBtn.addEventListener("click", toggleDarkMode);
  showMemoryBtn.addEventListener("click", showMemory);
  showDocListBtn.addEventListener("click", showDocs);
  closeMemoryBtn.addEventListener("click", () => memoryContainer.classList.remove("active"));
  closeDocBtn.addEventListener("click", () => sourceContainer.classList.remove("active"));
});