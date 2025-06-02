let currentClass = null;
let currentUsers = [];

// Load teacher's classes
async function loadClasses() {
  try {
    const response = await fetch('/teacher-classes', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) throw new Error('Failed to load classes');
    
    const data = await response.json();
    const selector = document.getElementById('class-selector');
    
    selector.innerHTML = '';
    if (data.classes.length === 0) {
      selector.innerHTML = '<option value="">No classes found</option>';
      return;
    }
    
    data.classes.forEach(cls => {
      const option = document.createElement('option');
      option.value = cls.name;
      option.textContent = cls.name;
      selector.appendChild(option);
    });
    
    // Set up event listener for class selection
    selector.addEventListener('change', async (e) => {
      currentClass = e.target.value;
      await loadClassUsers(currentClass);
    });
    
    // Load first class by default
    if (data.classes.length > 0) {
      currentClass = data.classes[0].name;
      selector.value = currentClass;
      await loadClassUsers(currentClass);
    }
  } catch (error) {
    console.error('Error loading classes:', error);
    alert('Failed to load classes');
  }
}

// Load users for selected class
async function loadClassUsers(classroom) {
  try {
    const response = await fetch(`/class-users/${classroom}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) throw new Error('Failed to load users');
    
    const data = await response.json();
    currentUsers = data.users;
    renderUsers();
    updateStats();
  } catch (error) {
    console.error('Error loading users:', error);
    alert('Failed to load users');
  }
}

// Render users in the UI
function renderUsers(filter = '') {
  const container = document.getElementById('users-container');
  container.innerHTML = '';
  
  const filteredUsers = currentUsers.filter(user => 
    user.name.toLowerCase().includes(filter.toLowerCase()) ||
    user.username.toLowerCase().includes(filter.toLowerCase())
  );
  
  if (filteredUsers.length === 0) {
    container.innerHTML = '<div class="text-muted">No users found</div>';
    return;
  }
  
  filteredUsers.forEach(user => {
    const userItem = document.createElement('div');
    userItem.className = `user-item d-flex justify-content-between align-items-center p-2 border rounded mb-2 ${user.is_active ? 'bg-light' : 'text-muted'}`;
    
    userItem.innerHTML = `
      <div>
        <span>${user.name}</span>
        <small class="d-block text-muted">${user.username}</small>
        <small class="d-block">Last active: ${formatDate(user.last_login)}</small>
      </div>
      <button class="toggle-access btn btn-sm ${user.access_enabled ? 'btn-danger' : 'btn-success'}" 
              data-username="${user.username}">
        ${user.access_enabled ? 'Disable Access' : 'Enable Access'}
      </button>
    `;
    
    container.appendChild(userItem);
  });
  
  // Add event listeners to buttons
  document.querySelectorAll('.toggle-access').forEach(button => {
    button.addEventListener('click', async function() {
      const username = this.dataset.username;
      const enable = !this.classList.contains('btn-success');
      
      try {
        const response = await fetch('/toggle-user-access', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ username, enable })
        });
        
        if (!response.ok) throw new Error('Failed to update access');
        
        // Update local data and re-render
        const user = currentUsers.find(u => u.username === username);
        if (user) user.access_enabled = enable;
        renderUsers(document.getElementById('search-bar').value);
      } catch (error) {
        console.error('Error toggling access:', error);
        alert('Failed to update access');
      }
    });
  });
}

// Update statistics cards
function updateStats() {
  const activeCount = currentUsers.filter(user => user.is_active).length;
  document.getElementById('active-users-count').textContent = activeCount;
  document.getElementById('total-users-count').textContent = currentUsers.length;
}

// Format date for display
function formatDate(isoString) {
  if (!isoString) return 'Never';
  const date = new Date(isoString);
  return date.toLocaleString();
}

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', async () => {
//   // Load user info
//   const token = localStorage.getItem('token');
//   if (!token) {
//     window.location.href = 'login.html';
//     return;
//   }
  
//   try {
//     // Load classes and initial data
//     await loadClasses();
    
//     // Set up search
//     document.getElementById('search-bar').addEventListener('input', (e) => {
//       renderUsers(e.target.value);
//     });
//   } catch (error) {
//     console.error('Initialization error:', error);
//   }
});