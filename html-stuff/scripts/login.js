    // Get the form element
    const loginForm = document.getElementById('loginForm');

    // Add event listener for form submission
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault(); // Prevent the form from refreshing the page

      // Get the form data
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;

      // Create the request body
      const body = {
        username: username,
        password: password
      };

      try {
        const response = await fetch('http://localhost:8053/verify_user', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body) // Send as JSON
        });

        if (response.ok) {
          const data = await response.json();

          // Store access token and username in localStorage
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('username', username);

          // Redirect to chat.html
          window.location.href = 'chat.html';
        } else {
          alert('Login failed: ' + response.statusText);
        }
      } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
      }
    });



    document.addEventListener("DOMContentLoaded", () => {
      const preloader = document.getElementById("preloader");
      const mainContent = document.getElementById("main-content");
    
      // Wait for the fade-out animation to complete
      preloader.addEventListener("animationend", () => {
        preloader.style.display = "none";
        mainContent.style.display = "block";
      });
    });
    