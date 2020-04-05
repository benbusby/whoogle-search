document.addEventListener("DOMContentLoaded", function() {

    // Setup search field
    const searchBar = document.getElementById("search-bar");
    const searchBtn = document.getElementById("search-submit");

    // Automatically focus on search field
    searchBar.focus();
    searchBar.select();

    searchBar.addEventListener("keyup", function(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            searchBtn.click();
        }
    });

    searchBtn.onclick = function() {
        window.location.href = '/search?q=' + encodeURI(searchBar.value);
    };

    // Setup shoogle config
    const saveConfig = document.getElementById("config-submit");
    const nearConfig = document.getElementById("config-near");

    // Request existing config info
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/static/config.json");
    xhr.onload = function() {
        if (xhr.readyState === 4 && xhr.status !== 200) {
            alert("Error loading Shoogle config");
            return;
        }

        // Allow for updating/saving config values
        let configSettings = JSON.parse(xhr.responseText);

        nearConfig.value = configSettings["near"];
        nearConfig.addEventListener("keyup", function(event) {
            configSettings["near"] = nearConfig.value;
        });

        saveConfig.onclick = function() {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/config");
            xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhr.send(JSON.stringify(configSettings));
        }
    };
    xhr.send();

});
