document.addEventListener("DOMContentLoaded", () => {
    const searchBar = document.getElementById("search-bar");
    const countrySelect = document.getElementById("result-country");
    const arrowKeys = [37, 38, 39, 40];
    let searchValue = searchBar.value;

    countrySelect.onchange = () => {
        let str = window.location.href;
        n = str.lastIndexOf("/search");
        if (n > 0) {
            str = str.substring(0, n) +
                `search?q=${searchBar.value}&country=${countrySelect.value}`;
            window.location.href = str;
        }
    }

    searchBar.addEventListener("keyup", function(event) {
        if (event.keyCode === 13) {
            document.getElementById("search-form").submit();
        } else if (searchBar.value !== searchValue && !arrowKeys.includes(event.keyCode)) {
            searchValue = searchBar.value;
            handleUserInput();
        }
    });
});
