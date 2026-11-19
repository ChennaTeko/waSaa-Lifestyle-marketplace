const BACKEND_URL = 'http://localhost:8000'; // Change this port if your backend runs on something else (e.g., 3000, 5000)

// Global function to close the OTP modal safely
function closeOTPModal() {
  const modal = document.getElementById('otpModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

// Toggle between Login and Sign Up views
function switchTab(tab) {
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  const loginBtn = document.getElementById('loginTabBtn');
  const signupBtn = document.getElementById('signupTabBtn');

  if (tab === 'login') {
    if (loginForm) loginForm.classList.remove('hidden');
    if (signupForm) signupForm.classList.add('hidden');
    if (loginBtn) loginBtn.classList.add('active');
    if (signupBtn) signupBtn.classList.remove('active');
  } else {
    if (signupForm) signupForm.classList.remove('hidden');
    if (loginForm) loginForm.classList.add('hidden');
    if (signupBtn) signupBtn.classList.add('active');
    if (loginBtn) loginBtn.classList.remove('active');
  }
}

// 1. Regular Email/Password Login Submission
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail')?.value;
  const password = document.getElementById('loginPassword')?.value;

  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok) {
      alert('Login successful!');
      localStorage.setItem('user', JSON.stringify(data.user));
      window.location.href = 'index.html';
    } else {
      alert(data.message || 'Login failed');
    }
  } catch (err) {
    console.error(err);
    alert('Server error. Please try again later.');
  }
});

// 2. Request OTP for Registration
async function requestOTP(e) {
  // If called from an event listener or inline onclick="requestOTP(event)"
  if (e && typeof e.preventDefault === 'function') {
    e.preventDefault();
  }

  const email = document.getElementById('signupEmail')?.value;
  const phone = document.getElementById('signupPhone')?.value;

  if (!email || !phone) {
    alert('Please fill in both email and phone number.');
    return;
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/request-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, phone })
    });
    const data = await res.json();
    if (res.ok) {
      alert('OTP sent successfully!');
      document.getElementById('otpModal')?.classList.remove('hidden');
    } else {
      alert(data.message || 'Failed to send OTP.');
    }
  } catch (err) {
    console.error(err);
    alert('Server error sending OTP.');
  }
}

// 3. Verify OTP and Register
async function verifyOTPAndRegister() {
  const name = document.getElementById('signupName')?.value || '';
  const email = document.getElementById('signupEmail')?.value || '';
  const phone = document.getElementById('signupPhone')?.value || '';
  const password = document.getElementById('signupPassword')?.value || '';
  const otp = document.getElementById('otpInput')?.value || '';

  if (!otp) {
    alert('Please enter the 6-digit OTP code.');
    return;
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, password, otp })
    });
    
    const data = await res.json();
    
    if (res.ok) {
      alert('Account created successfully!');
      closeOTPModal(); // Now works because it is in the global scope!
      
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      window.location.href = 'index.html';
    } else {
      alert(data.message || 'Invalid OTP');
    }
  } catch (err) {
    console.error('Verification error details:', err);
    alert('Verification error.');
  }
}

// 4. Handle Google Sign-In Callback
async function handleGoogleSignIn(response) {
  const credential = response.credential;
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: credential })
    });
    const data = await res.json();
    if (res.ok) {
      alert('Google Sign-In successful!');
      localStorage.setItem('user', JSON.stringify(data.user));
      window.location.href = 'index.html';
    } else {
      alert(data.message || 'Google Auth failed');
    }
  } catch (err) {
    console.error(err);
    alert('Google Authentication error.');
  }
}
