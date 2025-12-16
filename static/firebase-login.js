'use strict';

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCUUpy7bVTuQpuRonRrUa5tE8jVTtjbl5k",
  authDomain: "assignment-db79e.firebaseapp.com",
  projectId: "assignment-db79e",
  storageBucket: "assignment-db79e.firebasestorage.app",
  messagingSenderId: "1025418123592",
  appId: "1:1025418123592:web:fd4ef53d721873fa323b7d",
};

function setTokenCookie(token) {
  // Only set Secure when the site is actually served over HTTPS
  const secure = (location.protocol === "https:") ? "; Secure" : "";
  // Lax is usually best for normal web apps
  document.cookie = `token=${token}; Path=/; SameSite=Lax${secure}`;
}

function clearTokenCookie() {
  const secure = (location.protocol === "https:") ? "; Secure" : "";
  document.cookie = `token=; Max-Age=0; Path=/; SameSite=Lax${secure}`;
}

function parseCookieToken(cookie) {
  const parts = cookie.split(';');
  for (let i = 0; i < parts.length; i++) {
    const kv = parts[i].split('=');
    if (kv[0] && kv[0].trim() === "token") {
      return (kv[1] || "").trim();
    }
  }
  return "";
}

function updateUI() {
  const token = parseCookieToken(document.cookie);

  const loginBox = document.getElementById("login_box");
  const signOutBtn = document.getElementById("sign-out");

  if (token && token.length > 0) {
    if (loginBox) loginBox.hidden = true;
    if (signOutBtn) signOutBtn.hidden = false;
  } else {
    if (loginBox) loginBox.hidden = false;
    if (signOutBtn) signOutBtn.hidden = true;
  }
}

window.addEventListener("load", function () {
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);

  updateUI();

  const signupBtn = document.getElementById("sign-up");
  const loginBtn = document.getElementById("login");
  const signOutBtn = document.getElementById("sign-out");

  if (signupBtn) {
    signupBtn.addEventListener("click", async function () {
      const emailEl = document.getElementById("email");
      const passEl = document.getElementById("password");

      const email = emailEl ? emailEl.value : "";
      const password = passEl ? passEl.value : "";

      try {
        const userCredentials = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredentials.user;
        const token = await user.getIdToken();
        setTokenCookie(token);
        window.location = "/";
      } catch (error) {
        console.error(error.code, error.message);
        alert(error.message);
      }
    });
  }

  if (loginBtn) {
    loginBtn.addEventListener("click", async function () {
      const emailEl = document.getElementById("email");
      const passEl = document.getElementById("password");

      const email = emailEl ? emailEl.value : "";
      const password = passEl ? passEl.value : "";

      try {
        const userCredentials = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredentials.user;
        const token = await user.getIdToken();
        setTokenCookie(token);
        window.location = "/";
      } catch (error) {
        console.error(error.code, error.message);
        alert(error.message);
      }
    });
  }

  if (signOutBtn) {
    signOutBtn.addEventListener("click", async function () {
      try {
        await signOut(auth);
      } catch (error) {
        // Even if Firebase signOut fails, still clear the cookie
        console.error(error.code, error.message);
      }
      clearTokenCookie();
      window.location = "/";
    });
  }
});
