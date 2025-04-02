/**
 * ChatRagi Frontend Scripts
 *
 * This script handles the UI interactions for the ChatRagi chatbot interface.
 * It sends user queries to the backend, renders responses, manages memory display,
 * refreshes the document index, and displays the list of source documents.
 */

// UI Element References
const sendBtn = document.getElementById("send-btn");
const refreshBtn = document.getElementById("refresh-btn");
const showMemoryBtn = document.getElementById("show-memory-btn");
const closeMemoryBtn = document.getElementById("close-memory-btn");
const clearChatBtn = document.getElementById("clear-chat-btn");
const userInput = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");
const memoryContainer = document.getElementById("memory-container");
const memoryBox = document.getElementById("memory-box");
const showDocListBtn = document.getElementById("show-doc-list");
const closeDocListBtn = document.getElementById("close-doc-btn");
const sourceContainer = document.getElementById("source-container");
const sourceBox = document.getElementById("source-box");

/**
 * Scrolls the chat box to the bottom.
 */
const scrollToBottom = () => {
  chatBox.scrollTop = chatBox.scrollHeight;
};

/**
 * Sends a user query to the backend and renders the chatbot response.
 *
 * The function clears the input field immediately after the query is captured,
 * displays the user's query, sends the query to the backend, processes the response,
 * and then updates the UI with the formatted response.
 */
async function sendMessage() {
  const query = userInput.value.trim();
  if (!query) return;

  // Clear the input field immediately upon sending
  userInput.value = "";

  // Display the user's query in the chat box
  chatBox.innerHTML += `<div><strong>You:</strong> ${query}</div>`;
  scrollToBottom();

  try {
    // Send the query to the backend API endpoint
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await response.json();

    if (data.error) {
      chatBox.innerHTML += `<div><strong>Error:</strong> ${data.error}</div>`;
    } else {
      // Parse and render the chatbot's Markdown-formatted response using Marked.js
      const formattedResponse = marked.parse(data.answer);
      chatBox.innerHTML += `
        <div>
          <strong><br>ChatRagi:</strong>
          <div>${formattedResponse}</div>
          <hr>
        </div>`;
      scrollToBottom();

      // After a brief delay, prompt the user to mark the conversation as important
      setTimeout(async () => {
        const markImportant = confirm("Mark this conversation as important?");
        await storeMemory(query, data.answer, markImportant);
      }, 100);
    }
  } catch (error) {
    chatBox.innerHTML += `<div><strong>Error:</strong> Unable to fetch response.</div>`;
    scrollToBottom();
  }
}

/**
 * Stores the chatbot conversation in the backend.
 *
 * @param {string} user_query - The user's query.
 * @param {string} response - The chatbot's response.
 * @param {boolean} is_important - Indicates if the conversation should be marked as important.
 */
async function storeMemory(user_query, response, is_important) {
  try {
    const res = await fetch("/store-memory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_query, response, is_important })
    });
    const data = await res.json();
    if (data.status !== "success") {
      console.error("Failed to store memory:", data.error);
    }
  } catch (error) {
    console.error("Error in storeMemory:", error);
  }
}

/**
 * Sends a request to refresh the document index.
 */
async function refreshIndex() {
  try {
    const response = await fetch("/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();
    alert(data.response);
  } catch (error) {
    alert("Error refreshing index.");
  }
}

/**
 * Shows memory container and hides source container.
 */
async function showAllMemories() {
  sourceContainer.classList.remove("active");  // Collapse source panel
  memoryContainer.classList.add("active");     // Expand memory panel
  memoryBox.innerHTML = "<p>Loading memories...</p>";

  try {
    const response = await fetch("/all-memories");
    const data = await response.json();
    memoryBox.innerHTML = "";

    if (!data.memories || data.memories.length === 0) {
      memoryBox.innerHTML = "<p>No memory found.</p>";
    } else {
      data.memories.forEach(entry => {
        memoryBox.innerHTML += `
          <div>
            <p><strong>${new Date(entry.timestamp).toLocaleString()}</strong></p>
            <p><strong>User Query:</strong> ${entry.user_query}</p>
            <p><strong>Conversation:</strong> ${entry.conversation}</p>
            <p><strong>Important:</strong> ${entry.important ? "Yes" : "No"}</p>
            <hr>
          </div>`;
      });
    }
  } catch (error) {
    memoryBox.innerHTML = "<p>Error loading memories.</p>";
  }
}

/**
 * Shows the source container and hides the memory container.
 */
async function showDocList() {
  memoryContainer.classList.remove("active");  // Collapse memory panel
  sourceContainer.classList.add("active");     // Expand source panel
  sourceBox.innerHTML = "<p>Loading document list...</p>";

  try {
    const response = await fetch("/list-documents");
    const data = await response.json();
    sourceBox.innerHTML = "";

    if (!data.documents || data.documents.length === 0) {
      sourceBox.innerHTML = "<p>No document found.</p>";
    } else {
      data.documents.forEach(doc => {
        sourceBox.innerHTML += `<div><p>${doc}</p></div>`;
      });
    }
  } catch (error) {
    sourceBox.innerHTML = `<p>Error loading document list: ${error.message}</p>`;
  }
}

/**
* Closes the source document list with animation.
*/
function closeDocList() {
  sourceContainer.classList.remove("active");
  sourceBox.innerHTML = "";
}

/**
* Closes the memory panel with animation.
*/
function closeMemory() {
  memoryContainer.classList.remove("active");
  memoryBox.innerHTML = "";
}

/**
 * Clears the chat box of all messages.
 */
function clearChat() {
  chatBox.innerHTML = "";
}

// Attach event listeners for user interactions
sendBtn.addEventListener("click", sendMessage);
refreshBtn.addEventListener("click", refreshIndex);
showMemoryBtn.addEventListener("click", showAllMemories);
closeMemoryBtn.addEventListener("click", closeMemory);
clearChatBtn.addEventListener("click", clearChat);
showDocListBtn.addEventListener("click", showDocList);
closeDocListBtn.addEventListener("click", closeDocList);

/**
 * Listens for the "Enter" key to send a message.
 */
userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendMessage();
  }
});