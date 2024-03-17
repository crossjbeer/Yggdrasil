// script.js
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("password").addEventListener("input", function() {
        var password = this.value;
        var passwordRegex = /^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*])[A-Za-z0-9!@#$%^&*]{13,}$/;

        if (!passwordRegex.test(password)) {
            this.setCustomValidity("Password Requirements: At least 13 Characters | 1 Uppsercase Letter | 1 Digit | 1 Special Character (!@#$%^&*)");
        } else {
            this.setCustomValidity("");
        }
    });
});