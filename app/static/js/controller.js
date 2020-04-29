document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        document.getElementById("main").style.display = "block";
    }, 100);

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

    // Setup shoogle config
    const collapsible = document.getElementById("config-collapsible");
    collapsible.addEventListener("click", function() {
        this.classList.toggle("active");
        let content = this.nextElementSibling;
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = content.scrollHeight + "px";
        }

        content.classList.toggle("open");
    });

    const saveConfig = document.getElementById("config-submit");
    const nearConfig = document.getElementById("config-near");
    const noJSConfig = document.getElementById("config-nojs");
    const darkConfig = document.getElementById("config-dark");

    // Request existing config info
    let xhrGET = new XMLHttpRequest();
    xhrGET.open("GET", "/config");
    xhrGET.onload = function() {
        if (xhrGET.readyState === 4 && xhrGET.status !== 200) {
            alert("Error loading Shoogle config");
            return;
        }

        // Allow for updating/saving config values
        let configSettings = JSON.parse(xhrGET.responseText);

        nearConfig.value = configSettings["near"] ? configSettings["near"] : "";
        nearConfig.addEventListener("keyup", function() {
            configSettings["near"] = nearConfig.value;
        });

        noJSConfig.checked = !!configSettings["nojs"];
        noJSConfig.addEventListener("change", function() {
           configSettings["nojs"] = noJSConfig.checked ? 1 : 0;
        });

        darkConfig.checked = !!configSettings["dark"];
        darkConfig.addEventListener("change", function() {
           configSettings["dark"] = darkConfig.checked ? 1 : 0;
        });

        saveConfig.onclick = function() {
            let xhrPOST = new XMLHttpRequest();
            xhrPOST.open("POST", "/config");
            xhrPOST.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhrPOST.send(JSON.stringify(configSettings));
            xhrPOST.onload = function() {
                if (xhrGET.readyState === 4 && xhrPOST.status !== 200) {
                    alert("Failure to save config file");
                    return;
                }

                if (confirm("Configuration saved. Reload now?")) {
                    window.location.reload();
                }
            }
        }
    };
    xhrGET.send();

});
