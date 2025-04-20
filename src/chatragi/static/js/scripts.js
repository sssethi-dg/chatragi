
/**
 * ChatRagi Enhanced Frontend Script
 * Handles chat submission, memory toggling, downloads, dark mode, and source listing.
 */

// DOM references
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

// Helper: Scroll chat to latest
const scrollToBottom = () => {
  chatBox.scrollTop = chatBox.scrollHeight;
};

// Send query
async function sendMessage() {
  const query = userInput.value.trim();
  if (!query) return;
  chatBox.innerHTML += `<div class="user-message"><strong>You:</strong> ${query}</div>`;
  userInput.value = "";
  scrollToBottom();

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();

    if (data.error) {
      chatBox.innerHTML += `<div class="ai-message"><strong>Error:</strong> ${data.error}</div>`;
    } else {
      const answer = marked.parse(data.answer);
      chatBox.innerHTML += `<div class="ai-message"><strong>ChatRagi:</strong><div>${answer}</div></div><hr>`;
      scrollToBottom();
    }
  } catch {
    chatBox.innerHTML += `<div class="ai-message"><strong>Error:</strong> Server unreachable.</div>`;
  }
}

// Store chat memory (triggered from another UI event)
async function storeMemory(markImportant = false) {
  const lastUser = document.querySelector(".user-message:last-child");
  const lastAI = document.querySelector(".ai-message:last-child");
  if (!lastUser || !lastAI) return;

  try {
    await fetch("/store-memory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_query: lastUser.innerText.replace("You:", "").trim(),
        response: lastAI.innerText.replace("ChatRagi:", "").trim(),
        is_important: markImportant,
      }),
    });
  } catch (err) {
    console.error("Memory store failed", err);
  }
}

// Export chat content
function downloadChat() {
  const text = chatBox.innerText.trim();
  const blob = new Blob([text], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "chatragi_session.txt";
  a.click();
}

// Toggle light/dark mode
function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
}

// Clear chat box
function clearChat() {
  chatBox.innerHTML = "";
}

// Refresh backend index
async function refreshIndex() {
  const res = await fetch("/refresh", { method: "POST" });
  const data = await res.json();
  alert(data.response);
}

// Load all memory records
async function showMemory() {
  memoryBox.innerHTML = "<p>Loading...</p>";
  sourceContainer.classList.remove("active");
  memoryContainer.classList.add("active");

  try {
    const res = await fetch("/all-memories");
    const data = await res.json();
    memoryBox.innerHTML = data.memories.length
      ? data.memories.map(
          (m) => `
      <div>
        <p><strong>${new Date(m.timestamp).toLocaleString()}</strong></p>
        <p><strong>Q:</strong> ${m.user_query}</p>
        <p><strong>A:</strong> ${m.conversation}</p>
        <p><strong>Important:</strong> ${m.important ? "Yes" : "No"}</p>
        <hr>
      </div>`
        ).join("")
      : "<p>No memory found.</p>";
  } catch {
    memoryBox.innerHTML = "<p>Error loading memory.</p>";
  }
}

// Load document list
async function showDocs() {
  memoryContainer.classList.remove("active");
  sourceContainer.classList.add("active");
  sourceBox.innerHTML = "<p>Loading documents...</p>";

  try {
    const res = await fetch("/list-documents");
    const data = await res.json();
    sourceBox.innerHTML = data.documents.length
      ? data.documents.map((d) => `<p>${d}</p>`).join("")
      : "<p>No documents indexed.</p>";
  } catch (e) {
    sourceBox.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// Event bindings
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => e.key === "Enter" && sendMessage());
clearChatBtn.addEventListener("click", clearChat);
refreshBtn.addEventListener("click", refreshIndex);
markImportantBtn.addEventListener("click", () => storeMemory(true));
downloadBtn.addEventListener("click", downloadChat);
themeToggleBtn.addEventListener("click", toggleDarkMode);
showMemoryBtn.addEventListener("click", showMemory);
showDocListBtn.addEventListener("click", showDocs);
closeMemoryBtn.addEventListener("click", () => memoryContainer.classList.remove("active"));
closeDocBtn.addEventListener("click", () => sourceContainer.classList.remove("active"));
