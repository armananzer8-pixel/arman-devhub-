document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("greetButton");

    if (button) {
        button.addEventListener("click", function () {
            alert("Hello! Welcome to Day 157 of Django!");
        });
    }

});