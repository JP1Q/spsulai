// Get username from localStorage
const username = localStorage.getItem("username");
const userEmailElement = document.getElementById("user-email");
const userNameElement = document.getElementById("user-name");
const logoutBtn = document.getElementById("logout");
const teacherBtn = document.getElementById("teacher");
const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("message-input");
let chat_bubble_id = 0;

// Send a message from the user
function sendMessage() {
  const userMessage = messageInput.value.trim();
  if (!userMessage) return;

  // Add user message to chat
  addChatBubble("user", userMessage);
  let current_id = addChatBubble("ai", `<img src="scripts/loading.gif" alt="Loading..." />`);

  // Clear input field
  messageInput.value = "";

  // Send the message to the backend
  fetch("http://localhost:8052/generate_response", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "llama2-uncensored",
      prompt: userMessage,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      // Add AI response to chat
      setChatBubble(current_id, data.response || "Sorry, I couldn't generate a response.");
    })
    .catch((error) => {
      console.error("Error communicating with the backend:", error);
      setChatBubble(current_id, "There was an error processing your request.");
    });
}

// Add a chat bubble to the chat container
function addChatBubble(sender, content) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${sender}`;
  chat_bubble_id++;
  bubble.id = `bubble-${chat_bubble_id}`;

  // Set content: handle text or HTML (e.g., images)
  if (content.startsWith("<")) {
    bubble.innerHTML = content; // For HTML content like images
  } else {
    bubble.textContent = content; // For plain text
  }

  chatContainer.appendChild(bubble);

  // Scroll to the latest message
  chatContainer.scrollTop = chatContainer.scrollHeight;
  return bubble.id;
}

// Update the content of an existing chat bubble
function setChatBubble(id, message) {
  const bubble = document.getElementById(id);
  if (bubble) {
    if (message.startsWith("<")) {
      bubble.innerHTML = message;
    } else {
      bubble.textContent = message;
    }
  }
}

// Pressing "Enter" sends the message
messageInput.addEventListener("keypress", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

let toclassBtn = "";
try {
  toclassBtn = document.getElementById("backtochat");
} catch (e) {
  console.log(e);
  toclassBtn = null;
}

// Display username and email
if (username) {
  let emailDomain = "";
  if (/\d/.test(username)) {
    emailDomain = "zak.spsul.cz"; // Domain for email
  } else {
    emailDomain = "spsul.cz"; // Domain for email
  }

  userEmailElement.textContent = `${username}@${emailDomain}`;
  userNameElement.textContent = username;
} else {
  // Redirect to login if no username found
  alert("You need to log in first.");
  window.location.href = "login.html";
}

// Logout functionality
function logout() {
  // Clear localStorage
  localStorage.removeItem("username");
  localStorage.removeItem("access_token");

  // Redirect to login page
  window.location.href = "login.html";
}

function forteachers() {
  window.location.href = "teacherdashboard.html";
}

function toclass() {
  window.location.href = "chat.html";
}

logoutBtn.addEventListener("click", logout);
try {
  teacherBtn.addEventListener("click", forteachers);
} catch (e) {
  toclassBtn.addEventListener("click", toclass);
}

document.addEventListener("DOMContentLoaded", () => {
  const preloader = document.getElementById("preloader");
  const mainContent = document.getElementById("main-content");

  // Wait for the fade-out animation to complete
  preloader.addEventListener("animationend", () => {
    preloader.style.display = "none";
    mainContent.style.display = "block";
  });
});
