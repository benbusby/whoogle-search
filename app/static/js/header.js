document.addEventListener("DOMContentLoaded", () => {
    const searchBar = document.getElementById("search-bar");
    const arrowKeys = [37, 38, 39, 40];
    let searchValue = searchBar.value;

    searchBar.addEventListener("keyup", function(event) {
        if (event.keyCode === 13) {
            document.getElementById("search-form").submit();
        } else if (searchBar.value !== searchValue && !arrowKeys.includes(event.keyCode)) {
            searchValue = searchBar.value;
            handleUserInput();
        }
    });
});
