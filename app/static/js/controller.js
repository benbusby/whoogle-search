const setupSearchLayout = () => {
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
}

const fillConfigValues = (near, nojs, dark) => {
    // Request existing config info
    let xhrGET = new XMLHttpRequest();
    xhrGET.open("GET", "/config");
    xhrGET.onload = function() {
        if (xhrGET.readyState === 4 && xhrGET.status !== 200) {
            alert("Error loading Whoogle config");
            return;
        }

        // Allow for updating/saving config values
        let configSettings = JSON.parse(xhrGET.responseText);

        near.value = configSettings["near"] ? configSettings["near"] : "";
        near.addEventListener("keyup", function() {
            configSettings["near"] = near.value;
        });

        nojs.checked = !!configSettings["nojs"];
        nojs.addEventListener("change", function() {
           configSettings["nojs"] = nojs.checked ? 1 : 0;
        });

        dark.checked = !!configSettings["dark"];
        dark.addEventListener("change", function() {
           configSettings["dark"] = dark.checked ? 1 : 0;
        });
    };

    xhrGET.send();
}

const setupConfigLayout = () => {
    // Setup whoogle config
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

    const near = document.getElementById("config-near");
    const noJS = document.getElementById("config-nojs");
    const dark = document.getElementById("config-dark");

    fillConfigValues(near, noJS, dark);
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        document.getElementById("main").style.display = "block";
    }, 100);

    setupSearchLayout();
    setupConfigLayout();
});
