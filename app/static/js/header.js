document.addEventListener("DOMContentLoaded", () => {
    const searchBar = document.getElementById("search-bar");

    searchBar.addEventListener("keyup", function (event) {
        if (event.keyCode !== 13) {
            handleUserInput(searchBar);
        } else {
            document.getElementById("search-form").submit();
        }
    });
});
