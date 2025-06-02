// Get the form element
const loginForm = document.getElementById('loginForm');

// Function to get the server IP and port dynamically
async function getServerAddress() {
    const currentHost = window.location.hostname;
    const currentPort = "8053";
    
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        return `http://${currentHost}:${currentPort}`;
    }
    
    const possibleIPs = [
        'localhost',
        window.location.hostname,
        location.host.split(':')[0]
    ];
    return `http://${possibleIPs[0]}:${currentPort}`;
}

// Login handler
loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const body = { username, password };

    try {
        const serverUrl = await getServerAddress();
        const response = await fetch(`${serverUrl}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (response.status === 403) {
            const data = await response.json();
            if (data.detail === "Waiting for admin approval") {
                showApprovalPending();
                return;
            }
        }
        
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

// Admin: Manage classroom
async function manageClassroom(classroom, status) {
    const serverUrl = await getServerAddress();
    const response = await fetch(`${serverUrl}/manage-classroom`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ classroom, status })
    });
    
    if (!response.ok) {
        alert('Failed to update classroom status');
    }
}

// Fetch students in a class
async function fetchClassStudents(classroom) {
    const serverUrl = await getServerAddress();
    const response = await fetch(`${serverUrl}/class-students/${classroom}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    });
    
    if (!response.ok) {
        alert('Failed to fetch students');
        return [];
    }
    
    return await response.json();
}

// Display admin approval pending notice
function showApprovalPending() {
    alert('Your account is awaiting admin approval.');
}
