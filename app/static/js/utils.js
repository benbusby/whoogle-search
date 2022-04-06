const checkForTracking = () => {
    const mainDiv = document.getElementById("main");
    const searchBar = document.getElementById("search-bar");
    // some pages (e.g. images) do not have these
    if (!mainDiv || !searchBar)
        return;
    const query = searchBar.value.replace(/\s+/g, '');

    // Note: regex functions for checking for tracking queries were derived
    // from here -- https://stackoverflow.com/questions/619977
    const matchTracking = {
        "ups": {
            "link": `https://www.ups.com/track?tracknum=${query}`,
            "expr": [
                /\b(1Z ?[0-9A-Z]{3} ?[0-9A-Z]{3} ?[0-9A-Z]{2} ?[0-9A-Z]{4} ?[0-9A-Z]{3} ?[0-9A-Z]|[\dT]\d\d\d ?\d\d\d\d ?\d\d\d)\b/
            ]
        },
        "usps": {
            "link": `https://tools.usps.com/go/TrackConfirmAction?tLabels=${query}`,
            "expr": [
                /(\b\d{30}\b)|(\b91\d+\b)|(\b\d{20}\b)/,
                /^E\D{1}\d{9}\D{2}$|^9\d{15,21}$/,
                /^91[0-9]+$/,
                /^[A-Za-z]{2}[0-9]+US$/
            ]
        },
        "fedex": {
            "link": `https://www.fedex.com/apps/fedextrack/?tracknumbers=${query}`,
            "expr": [
                /(\b96\d{20}\b)|(\b\d{15}\b)|(\b\d{12}\b)/,
                /\b((98\d\d\d\d\d?\d\d\d\d|98\d\d) ?\d\d\d\d ?\d\d\d\d( ?\d\d\d)?)\b/,
                /^[0-9]{15}$/
            ]
        }
    };
    
    // Creates a link to a UPS/USPS/FedEx tracking page
    const createTrackingLink = href => {
        let link = document.createElement("a");
        link.className = "tracking-link";
        link.innerHTML = "View Tracking Info";
        link.href = href;
        mainDiv.prepend(link);
    };

    // Compares the query against a set of regex patterns
    // for tracking numbers
    const compareQuery = provider => {
        provider.expr.some(regex => {
            if (query.match(regex)) {
                createTrackingLink(provider.link);
                return true;
            }
        });
    };

    for (const key of Object.keys(matchTracking)) {
        compareQuery(matchTracking[key]);
    }
};

document.addEventListener("DOMContentLoaded", function() {
    checkForTracking();

    // Clear input if reset button tapped
    const searchBar = document.getElementById("search-bar");
    const resetBtn = document.getElementById("search-reset");
    // some pages (e.g. images) do not have these
    if (!searchBar || !resetBtn)
        return;
    resetBtn.addEventListener("click", event => {
        event.preventDefault();
        searchBar.value = "";
        searchBar.focus();
    });
});
