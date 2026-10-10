// ======================================
// SPWP FEEDBACK SYSTEM
// JavaScript for Flask Application
// ======================================


// --------------------------------------
// STUDENT LOGIN
// --------------------------------------
function studentLogin() {

    let studentId = document.getElementById("studentId").value;
    let password = document.getElementById("password").value;

    if (studentId.trim() === "" || password.trim() === "") {

        alert("Please enter Student ID and Password.");
        return;
    }

    // Send the login information to Flask
    document.getElementById("studentLoginForm").submit();
}


// --------------------------------------
// PARENT LOGIN
// --------------------------------------
function parentLogin() {

    let parentId = document.getElementById("parentId").value;
    let password = document.getElementById("password").value;

    if (parentId.trim() === "" || password.trim() === "") {

        alert("Please enter Parent ID and Password.");
        return;
    }

    // Send login information to Flask
    document.getElementById("parentLoginForm").submit();
}


// --------------------------------------
// LOGOUT
// --------------------------------------
function logout() {

    window.location.href = "/logout";

}