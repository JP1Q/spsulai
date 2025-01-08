// Get username from localStorage
const username = localStorage.getItem("username");
const userEmailElement = document.getElementById("user-email");
const userNameElement = document.getElementById("user-name");
const logoutBtn = document.getElementById("logout");
const teacherBtn = document.getElementById("teacher");
const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("message-input");
let chat_bubble_id = 0;

// Function to get the server address
async function getServerAddress() {
    const currentHost = window.location.hostname;
    const currentPort = "8052"; // Your backend port for chat

    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        return `http://${currentHost}:${currentPort}`;
    }

    // Use the current hostname if not localhost
    const serverUrl = `http://${window.location.hostname}:${currentPort}`;
    return serverUrl;
}

async function sendMessage() {
    const userMessage = messageInput.value.trim();
    if (!userMessage) return;

    // Add user message to chat
    addChatBubble("user", userMessage);
    let current_id = addChatBubble("ai", `<img src="scripts/loading.gif" alt="Loading..." />`);

    // Clear input field
    messageInput.value = "";

    try {
        // Get the server address dynamically
        const serverUrl = await getServerAddress();
        const response = await fetch(`${serverUrl}/generate_response`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                prompt: userMessage,
                model: "llama3-nogpu:latest"
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

            buffer += decoder.decode(value, { stream: true });
            setChatBubble(current_id, buffer);
        }
    } catch (error) {
        console.error("Error communicating with the backend:", error);
        setChatBubble(current_id, "There was an error processing your request.");
    }
}

// // Add debug information (can be removed in production)
// function showConnectionInfo() {
//     const debugInfo = document.createElement('div');
//     debugInfo.style.position = 'fixed';
//     debugInfo.style.bottom = '10px';
//     debugInfo.style.left = '10px';
//     debugInfo.style.backgroundColor = 'rgba(0,0,0,0.7)';
//     debugInfo.style.color = 'white';
//     debugInfo.style.padding = '10px';
//     debugInfo.style.borderRadius = '5px';
//     debugInfo.style.fontSize = '12px';
    
//     const updateInfo = async () => {
//         const serverUrl = await getServerAddress();
//         debugInfo.innerHTML = `
//             Current URL: ${window.location.href}<br>
//             Server URL: ${serverUrl}<br>
//             Hostname: ${window.location.hostname}<br>
//             Port: 8052
//         `;
//     };
    
//     updateInfo();
//     document.body.appendChild(debugInfo);
// }

// Rest of your existing functions remain the same
function addChatBubble(sender, content) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    chat_bubble_id++;
    bubble.id = `bubble-${chat_bubble_id}`;
    bubble.innerHTML = content.startsWith("<") ? content : escapeHtml(content);
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return bubble.id;
}

function setChatBubble(id, message) {
    const bubble = document.getElementById(id);
    if (bubble) {
        bubble.innerHTML = message.startsWith("<") ? message : escapeHtml(message);
    }
}

function escapeHtml(text) {
    const element = document.createElement('div');
    if (text) {
        element.innerText = text;
        element.textContent = text;
    }
    return element.innerHTML;
}

// Event listeners and initialization
messageInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

if (username) {
    const emailDomain = /\d/.test(username) ? "zak.spsul.cz" : "spsul.cz";
    userEmailElement.textContent = `${username}@${emailDomain}`;
    userNameElement.textContent = username;
} else {
    alert("You need to log in first.");
    window.location.href = "login.html";
}

function logout() {
    localStorage.removeItem("username");
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
}

function forteachers() {
    window.location.href = "teacherdashboard.html";
}

function toclass() {
    window.location.href = "chat.html";
}

logoutBtn.addEventListener("click", logout);
teacherBtn.addEventListener("click", forteachers);

document.addEventListener("DOMContentLoaded", () => {
    const teacherBtn = document.getElementById("teacher");
    const backToChatBtn = document.getElementById("backtochat");

    if (teacherBtn) teacherBtn.href = "teacherdashboard.html";
    if (backToChatBtn) backToChatBtn.href = "chat.html";
    
    // Add this line to show connection info (remove in production)
    showConnectionInfo();
});