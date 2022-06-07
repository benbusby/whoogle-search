let searchInput;
let currentFocus;
let originalSearch;
let autocompleteResults;

const handleUserInput = () => {
    let xhrRequest = new XMLHttpRequest();
    xhrRequest.open("POST", "autocomplete");
    xhrRequest.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhrRequest.onload = function () {
        if (xhrRequest.readyState === 4 && xhrRequest.status !== 200) {
            // Do nothing if failed to fetch autocomplete results
            return;
        }

        // Fill autocomplete with fetched results
        autocompleteResults = JSON.parse(xhrRequest.responseText)[1];
        updateAutocompleteList();
    };

    xhrRequest.send('q=' + searchInput.value);
};

const closeAllLists = el => {
    // Close all autocomplete suggestions
    let suggestions = document.getElementsByClassName("autocomplete-items");
    for (let i = 0; i < suggestions.length; i++) {
        if (el !== suggestions[i] && el !== searchInput) {
            suggestions[i].parentNode.removeChild(suggestions[i]);
        }
    }
};

const removeActive = suggestion => {
    // Remove "autocomplete-active" class from previously active suggestion
    for (let i = 0; i < suggestion.length; i++) {
        suggestion[i].classList.remove("autocomplete-active");
    }
};

const addActive = (suggestion) => {
    // Handle navigation outside of suggestion list
    if (!suggestion || !suggestion[currentFocus]) {
        if (currentFocus >= suggestion.length) {
            // Move selection back to the beginning
            currentFocus = 0;
        } else if (currentFocus < 0) {
            // Retrieve original search and remove active suggestion selection
            currentFocus = -1;
            searchInput.value = originalSearch;
            removeActive(suggestion);
            return;
        } else {
            return;
        }
    }

    removeActive(suggestion);
    suggestion[currentFocus].classList.add("autocomplete-active");

    // Autofill search bar with suggestion content (minus the "bang name" if using a bang operator)
    let searchContent = suggestion[currentFocus].textContent;
    if (searchContent.indexOf('(') > 0) {
        searchInput.value = searchContent.substring(0, searchContent.indexOf('('));
    } else {
        searchInput.value = searchContent;
    }

    searchInput.focus();
};

const autocompleteInput = (e) => {
    // Handle navigation between autocomplete suggestions
    let suggestion = document.getElementById(this.id + "-autocomplete-list");
    if (suggestion) suggestion = suggestion.getElementsByTagName("div");
    if (e.keyCode === 40) { // down
        e.preventDefault();
        currentFocus++;
        addActive(suggestion);
    } else if (e.keyCode === 38) { //up
        e.preventDefault();
        currentFocus--;
        addActive(suggestion);
    } else if (e.keyCode === 13) { // enter
        e.preventDefault();
        if (currentFocus > -1) {
            if (suggestion) suggestion[currentFocus].click();
        }
    } else {
        originalSearch = searchInput.value;
    }
};

const updateAutocompleteList = () => {
    let autocompleteList, autocompleteItem, i;
    let val = originalSearch;
    closeAllLists();

    if (!val || !autocompleteResults) {
        return false;
    }

    currentFocus = -1;
    autocompleteList = document.createElement("div");
    autocompleteList.setAttribute("id", this.id + "-autocomplete-list");
    autocompleteList.setAttribute("class", "autocomplete-items");
    searchInput.parentNode.appendChild(autocompleteList);

    for (i = 0; i < autocompleteResults.length; i++) {
        if (autocompleteResults[i].substr(0, val.length).toUpperCase() === val.toUpperCase()) {
            autocompleteItem = document.createElement("div");
            autocompleteItem.innerHTML = "<strong>" + autocompleteResults[i].substr(0, val.length) + "</strong>";
            autocompleteItem.innerHTML += autocompleteResults[i].substr(val.length);
            autocompleteItem.innerHTML += "<input type=\"hidden\" value=\"" + autocompleteResults[i] + "\">";
            autocompleteItem.addEventListener("click", function () {
                searchInput.value = this.getElementsByTagName("input")[0].value;
                closeAllLists();
                document.getElementById("search-form").submit();
            });
            autocompleteList.appendChild(autocompleteItem);
        }
    }
};

document.addEventListener("DOMContentLoaded", function() {
    searchInput = document.getElementById("search-bar");
    searchInput.addEventListener("keydown", (event) => autocompleteInput(event));

    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
});