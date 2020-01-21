document.addEventListener("DOMContentLoaded", function() {
    const searchBar = document.getElementById("search-bar");
    const searchBtn = document.getElementById("search-submit");

    searchBar.addEventListener("keyup", function(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            searchBtn.click();
        }
    });

    searchBtn.onclick = function() {
        window.location.href = '/search?q=' + encodeURI(searchBar.value);
    }
});
