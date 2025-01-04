// Get username from localStorage
const username = localStorage.getItem('username');
const userEmailElement = document.getElementById('user-email');
const userNameElement = document.getElementById('user-name');
const logoutBtn = document.getElementById('logout');
const teacherBtn = document.getElementById('teacher');
let toclassBtn = "";
try{
  toclassBtn = document.getElementById('backtochat');
}
catch(e){
  console.log(e);
  toclassBtn = null;
}

// Display username and email
if (username) {
  let emailDomain = "";
  if(/\d/.test(username)){
    emailDomain = "zak.spsul.cz"; // Domain for email
  }else{
    emailDomain = "spsul.cz"; // Domain for email
  }
  
  userEmailElement.textContent = `${username}@${emailDomain}`;
  userNameElement.textContent = username;
} else {
  // Redirect to login if no username found
  alert('You need to log in first.');
  window.location.href = 'login.html';
}

// Logout functionality
function logout() {
  // Clear localStorage
  localStorage.removeItem('username');
  localStorage.removeItem('access_token');

  // Redirect to login page
  window.location.href = 'login.html';
}


function forteachers(){
    window.location.href = 'teacherdashboard.html';
}

function toclass(){
  window.location.href = 'chat.html';
}

logoutBtn.addEventListener('click', logout);
try{
  teacherBtn.addEventListener('click', forteachers);
}
catch(e){
  toclassBtn.addEventListener('click', toclass);
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