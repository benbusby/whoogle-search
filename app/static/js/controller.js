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

const fillConfigValues = (near, nojs, dark, url) => {
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
        nojs.checked = !!configSettings["nojs"];
        dark.checked = !!configSettings["dark"];

        // Addresses the issue of incorrect URL being used behind reverse proxy
        url.value = configSettings["url"] ? configSettings["url"] : "";
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
    const url  = document.getElementById("config-url");

    fillConfigValues(near, noJS, dark, url);
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        document.getElementById("main").style.display = "block";
    }, 100);

    setupSearchLayout();
    setupConfigLayout();
});
