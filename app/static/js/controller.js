// Whoogle configurations that use boolean values and checkboxes
CONFIG_BOOLS = [
    "nojs", "dark", "safe", "alts", "new_tab", "get_only"
];

// Whoogle configurations that use string values and input fields
CONFIG_STRS = [
    "near", "url"
];


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
        } else {
            handleUserInput(searchBar);
        }
    });
};

const fillConfigValues = () => {
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

        CONFIG_STRS.forEach(function(item) {
            let configElement = document.getElementById("config-" + item.replace("_", "-"));
            configElement.value = configSettings[item] ? configSettings[item] : "";
        });

        CONFIG_BOOLS.forEach(function(item) {
            let configElement = document.getElementById("config-" + item.replace("_", "-"));
            configElement.checked = !!configSettings[item];
        });
    };

    xhrGET.send();
};

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

    fillConfigValues();
};

const loadConfig = event => {
    event.preventDefault();
    let config = prompt("Enter name of config:");
    if (!config) {
        alert("Must specify a name for the config to load");
        return;
    }

    let xhrPUT = new XMLHttpRequest();
    xhrPUT.open("PUT", "/config?name=" + config + ".conf");
    xhrPUT.onload = function() {
        if (xhrPUT.readyState === 4 && xhrPUT.status !== 200) {
            alert("Error loading Whoogle config");
            return;
        }

        location.reload(true);
    };

    xhrPUT.send();
};

const saveConfig = event => {
    event.preventDefault();
    let config = prompt("Enter name for this config:");
    if (!config) {
        alert("Must specify a name for the config to save");
        return;
    }

    let configForm = document.getElementById("config-form");
    configForm.action = '/config?name=' + config + ".conf";
    configForm.submit();
};

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        document.getElementById("main").style.display = "block";
    }, 100);

    setupSearchLayout();
    setupConfigLayout();

    // Focusing on the search input field requires a delay for elements to finish
    // loading (seemingly only on FF)
    setTimeout(function() { document.getElementById("search-bar").focus(); }, 250);
});
