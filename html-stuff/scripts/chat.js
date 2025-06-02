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
        return `http://localhost:${currentPort}`;
    }

    return `http://${window.location.hostname}:${currentPort}`;
}

// Initialize marked with default options
marked.setOptions({
    highlight: function (code, language) {
        if (language && hljs.getLanguage(language)) {
            try {
                return hljs.highlight(code, { language }).value;
            } catch (e) {
                console.error("Error highlighting code:", e);
                return code;
            }
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true,
    langPrefix: 'hljs language-',
    mangle: false,
    headerIds: false
});

// Function to preprocess markdown content before parsing
function preprocessMarkdown(markdown) {
    // Handle code blocks with language specification
    let processed = markdown.replace(/```(\w+)\s*([\s\S]*?)\s*```/g, (match, lang, code) => {
        // Escape the backticks inside code block content
        const escapedCode = code.replace(/`/g, '\\`');
        return `\n\`\`\`${lang}\n${escapedCode}\n\`\`\`\n`;
    });

    // Handle code blocks without language specification
    processed = processed.replace(/```\s*([\s\S]*?)\s*```/g, (match, code) => {
        // Escape the backticks inside code block content
        const escapedCode = code.replace(/`/g, '\\`');
        return `\n\`\`\`\n${escapedCode}\n\`\`\`\n`;
    });

    // Handle inline code
    processed = processed.replace(/`([^`]+)`/g, (match, code) => {
        // Escape backticks inside inline code
        const escapedCode = code.replace(/`/g, '\\`');
        return `\`${escapedCode}\``;
    });

    return processed;
}

// Function to parse markdown with code block support
function parseMarkdown(markdown) {
    try {
        // Preprocess the markdown content
        const processedMarkdown = preprocessMarkdown(markdown);
        
        // Parse the markdown
        const rawHtml = marked.parse(processedMarkdown);
        
        // Sanitize the HTML while preserving code blocks
        const cleanHtml = DOMPurify.sanitize(rawHtml, {
            ADD_TAGS: ['pre', 'code'],
            ADD_ATTR: ['class'],
            FORBID_TAGS: ['style', 'script'],
            FORBID_ATTR: ['style', 'onclick', 'onmouseover'],
        });
        
        return cleanHtml;
    } catch (error) {
        console.error("Error parsing markdown:", error);
        return markdown;
    }
}


// Function to enhance code blocks with copy buttons
function enhanceCodeBlocks(bubbleId) {
    const bubble = document.getElementById(bubbleId);
    if (!bubble) return;

    const codeBlocks = bubble.querySelectorAll('pre code');
    codeBlocks.forEach((codeBlock) => {
        // Skip if already enhanced
        if (codeBlock.parentElement.parentElement.classList.contains('code-block-wrapper')) {
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.textContent = 'Copy';
        copyButton.onclick = async () => {
            try {
                const codeContent = codeBlock.textContent;
                await navigator.clipboard.writeText(codeContent);
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code:', err);
                copyButton.textContent = 'Error';
            }
        };

        const pre = codeBlock.parentElement;
        wrapper.appendChild(copyButton);
        pre.parentElement.replaceChild(wrapper, pre);
        wrapper.appendChild(pre);
    });
}

// Add chat bubble
function addChatBubble(sender, content) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    chat_bubble_id++;
    bubble.id = `bubble-${chat_bubble_id}`;

    bubble.innerHTML = content.startsWith("<") ? content : parseMarkdown(content);
    chatContainer.appendChild(bubble);
    enhanceCodeBlocks(bubble.id);
    scrollToBottom();
    return bubble.id;
}

// Update an existing chat bubble
function setChatBubble(id, content) {
    const bubble = document.getElementById(id);
    if (bubble) {
        bubble.innerHTML = content.startsWith("<") ? content : parseMarkdown(content);
        enhanceCodeBlocks(id);
    }
    scrollToBottom();
}

// Scroll chat to the bottom
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
let abortController;  // Global variable to hold the controller for aborting the request

// Function to send a message
async function sendMessage() {
    const userMessage = messageInput.value.trim();
    if (!userMessage) return;

    const userBubbleId = addChatBubble("user", userMessage);
    const aiBubbleId = addChatBubble("ai", `<img src="scripts/loading.gif" width="20px" alt="Loading..." />`);
    messageInput.value = "";

    // Show the "Stop Generating" button when a request is in progress
    const stopButton = document.getElementById("stop-generating");
    stopButton.style.display = "inline-block";  // Show the stop button

    // Create an AbortController instance for this request
    abortController = new AbortController();
    const signal = abortController.signal;

    try {
        const serverUrl = await getServerAddress();
        const response = await fetch(`${serverUrl}/generate_response`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: userMessage, model: "tinyllama" }),
            signal: signal,  // Attach the abort signal to the fetch request
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
                if (!buffer) setChatBubble(aiBubbleId, "No response generated.");
                break;
            }
            buffer += decoder.decode(value, { stream: true });
            setChatBubble(aiBubbleId, buffer);
        }

        // Once all content is generated, apply syntax highlighting
        const bubble = document.getElementById(aiBubbleId);
        if (bubble) {
            // Ensure highlighting after all content is loaded
            const codeBlocks = bubble.querySelectorAll('pre code');
            codeBlocks.forEach((codeBlock) => {
                hljs.highlightElement(codeBlock);  // Apply highlighting to each code block
            });
        }

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Message generation was aborted.');
            // setChatBubble(aiBubbleId, "Generation stopped.");
        } else {
            console.error("Error communicating with the backend:", error);
            setChatBubble(aiBubbleId, "There was an error processing your request.");
        }
    } finally {
        // Hide the "Stop Generating" button after process is finished
        stopButton.style.display = "none";
    }
}

// Function to stop the generation process
function stopGenerating() {
    if (abortController) {
        abortController.abort();  // Abort the ongoing request
    }
}



// Event listeners for sending messages
messageInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// User info setup
if (username) {
    const emailDomain = /\d/.test(username) ? "zak.spsul.cz" : "spsul.cz";
    userEmailElement.textContent = `${username}@${emailDomain}`;
    userNameElement.textContent = username;
} else {
    alert("You need to log in first.");
    window.location.href = "login.html";
}

// Logout and teacher navigation
logoutBtn.addEventListener("click", () => {
    localStorage.clear();
    window.location.href = "login.html";
});

teacherBtn.addEventListener("click", () => {
    window.location.href = "teacherdashboard.html";
});

const RATING_DELAY = 5 * 1000; // 5 minutes

// Show rating popup after delay
setTimeout(() => {
  const popup = document.getElementById('ratingPopup');
  if (popup) popup.style.display = 'block';
}, RATING_DELAY);

// Attach click handlers to emoticons
document.querySelectorAll('#ratingPopup .emoticon').forEach(el => {
    el.addEventListener('click', async () => {
      const rating = el.dataset.rating;
      const host   = window.location.hostname;           // e.g. "127.0.0.1" or "localhost"
      const apiUrl = `http://${host}:8053`;               // only here we reference port 8053
  
      try {
        const token = localStorage.getItem('access_token');
        const res   = await fetch(
          `${apiUrl}/user/rating?rating=${rating}`,       // fully qualified URL
          {
            method:      'POST',
            mode:        'cors',
            credentials: 'include',
            headers: {
              'Content-Type':  'application/json',
              'Authorization': `Bearer ${token}`,
            },
          }
        );
        if (!res.ok) throw new Error(res.statusText);
  
        // Hide popup & thank the user
        document.getElementById('ratingPopup').style.display = 'none';
        addChatBubble('ai', 'Děkuji za hodnocení! 😊');
      } catch (err) {
        console.error('Chyba při odesílání hodnocení:', err);
        addChatBubble('ai', 'Nepodařilo se uložit hodnocení. Zkus to prosím znovu.');
      }
    });
  });
  
