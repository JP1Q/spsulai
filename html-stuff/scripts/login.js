// Get the form element
const loginForm = document.getElementById('loginForm');

// Function to get the server IP and port
async function getServerAddress() {
    // First try window.location to get the current server address
    const currentHost = window.location.hostname;
    const currentPort = "8053"; // Your backend port

    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        return `http://${currentHost}:${currentPort}`;
    }

    // Fallback to checking multiple local IPs
    const possibleIPs = [
        'localhost',
        window.location.hostname,
        location.host.split(':')[0]
    ];

    // Return the first working IP
    const serverUrl = `http://${possibleIPs[0]}:${currentPort}`;
    return serverUrl;
}

// Modified login handler
loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const body = {
        username: username,
        password: password
    };

    try {
        // Get the server address dynamically
        const serverUrl = await getServerAddress();
        const response = await fetch(`${serverUrl}/verify_user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('username', username);
            window.location.href = 'chat.html';
        } else {
            alert('Login failed: ' + response.statusText);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
});