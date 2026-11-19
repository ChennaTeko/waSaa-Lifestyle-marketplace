/* WaSaa front-end settings. This is the ONLY file you edit to connect the backend. */
window.WASAA_CONFIG = {
  // Leave empty until your backend exists. Then set e.g. "http://localhost:8000".
  // While empty, the forms validate input but tell the user the backend is not connected.
  API_BASE_URL: "",

  // POST endpoints your backend must provide (JSON in, JSON out).
  ENDPOINTS: {
    signup: "/api/auth/signup/",
    login: "/api/auth/login/",
    forgot: "/api/auth/password-reset/"
  },

  LOGIN_URL: "login.html",
  AFTER_LOGIN_URL: "index.html"   // change to your dashboard page when it exists
};