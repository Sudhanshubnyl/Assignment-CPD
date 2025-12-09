'use strict';

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyDs_lx4-SVnctJcyN1biAlzc1PxJ2tnQKE",
    authDomain: "cloud-assignment-1-414516.firebaseapp.com",
    projectId: "cloud-assignment-1-414516",
    storageBucket: "cloud-assignment-1-414516.appspot.com",
    messagingSenderId: "487762088869",
    appId: "1:487762088869:web:d881fb570a7555266c4e4c"
};

// firebase-login.js
window.addEventListener("load", function () {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);
    console.log("hello world load");

    document.getElementById("sign-up").addEventListener('click', function () {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        createUserWithEmailAndPassword(auth, email, password).then((userCredentials) => {
            const user = userCredentials.user;

            user.getIdToken().then((token) => {
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });
        }).catch((error) => {
            console.error(error.code, error.message);
        })
    });

    document.getElementById("login").addEventListener('click', function () {
        console.log("Login button clicked");
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        signInWithEmailAndPassword(auth, email, password)
            .then((userCredentials) => {
                const user = userCredentials.user;
                console.log("logged in");

                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                    window.location = "/";
                });
            })
            .catch((error) => {
                console.log(error.code + error.message);
            })
    });

    document.getElementById("sign-out").addEventListener('click', function () {
        signOut(auth).then(() => {
            document.cookie = "token=;path=/;SameSite=Strict";
            window.location = "/";
        });
    });


});


function updateUI(cookie) {
    var token = parseCookieToken(cookie);
    
    console.log("Token:", token);
    

    if (token.length>0) {
        console.log("User is authenticated. Showing electric vehicle content.");
         document.getElementById("login_box").hidden=true;
         document.getElementById("sign-out").hidden=false;
    } else {
        console.log("User is not authenticated. Hiding electric vehicle content.");
        document.getElementById("login_box").hidden=false;
        document.getElementById("sign-out").hidden=true;
    }
}


function parseCookieToken(cookie) {
    var strings = cookie.split(';');

    for (let i = 0; i < strings.length; i++) {
        var temp = strings[i].split('=');
        if (temp[0].trim() === "token") {
            return temp[1].trim();
        }
    }

    return "";
}