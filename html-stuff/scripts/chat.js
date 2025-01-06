// Get username from localStorage
const username = localStorage.getItem("username");
const userEmailElement = document.getElementById("user-email");
const userNameElement = document.getElementById("user-name");
const logoutBtn = document.getElementById("logout");
const teacherBtn = document.getElementById("teacher");
const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("message-input");
let chat_bubble_id = 0;

async function sendMessage() {
  const userMessage = messageInput.value.trim();
  if (!userMessage) return;

  // Add user message to chat
  addChatBubble("user", userMessage);
  let current_id = addChatBubble("ai", `<img src="scripts/loading.gif" alt="Loading..." />`);

  // Clear input field
  messageInput.value = "";

  // Send the message to the backend
  try {
    const response = await fetch("http://127.0.0.1:8052/generate_response", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: userMessage,
        model: "llama2-uncensored"  // Fixed model selection
      }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    let buffer = '';
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        if (!buffer) {
          setChatBubble(current_id, "Sorry, I couldn't generate a response.");
        }
        break;
      }

      // Decode the chunk and append it to the buffer
      buffer += decoder.decode(value, { stream: true });
      setChatBubble(current_id, buffer);
    }
  } catch (error) {
    console.error("Error communicating with the backend:", error);
    setChatBubble(current_id, "There was an error processing your request.");
  }
}



// Add a chat bubble to the chat container
function addChatBubble(sender, content) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${sender}`;
  chat_bubble_id++;
  bubble.id = `bubble-${chat_bubble_id}`;

  // Set content: handle text or HTML (e.g., images)
  bubble.innerHTML = content.startsWith("<") ? content : escapeHtml(content);

  chatContainer.appendChild(bubble);

  // Scroll to the latest message
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return bubble.id;
}

// Update the content of an existing chat bubble
function setChatBubble(id, message) {
  const bubble = document.getElementById(id);
  if (bubble) {
    bubble.innerHTML = message.startsWith("<") ? message : escapeHtml(message);
  }
}

// Function to escape HTML characters in messages
function escapeHtml(text) {
  const element = document.createElement('div');
  if (text) {
    element.innerText = text;
    element.textContent = text;
  }
  return element.innerHTML;
}

// Pressing "Enter" sends the message
messageInput.addEventListener("keypress", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

// Display username and email
if (username) {
  const emailDomain = /\d/.test(username) ? "zak.spsul.cz" : "spsul.cz";
  userEmailElement.textContent = `${username}@${emailDomain}`;
  userNameElement.textContent = username;
} else {
  alert("You need to log in first.");
  window.location.href = "login.html";
}

// Logout functionality
function logout() {
  localStorage.removeItem("username");
  localStorage.removeItem("access_token");
  window.location.href = "login.html";
}

// Navigate to teacher dashboard
function forteachers() {
  window.location.href = "teacherdashboard.html";
}

// Navigate back to chat
function toclass() {
  window.location.href = "chat.html";
}

logoutBtn.addEventListener("click", logout);
teacherBtn.addEventListener("click", forteachers);

// Dynamically set href attributes
document.addEventListener("DOMContentLoaded", () => {
  const teacherBtn = document.getElementById("teacher");
  const backToChatBtn = document.getElementById("backtochat");

  if (teacherBtn) teacherBtn.href = "teacherdashboard.html";
  if (backToChatBtn) backToChatBtn.href = "chat.html";
});
