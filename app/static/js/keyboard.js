(function () {
    let searchBar, results;
    let shift = false;
    const keymap = {
        ArrowUp: goUp,
        ArrowDown: goDown,
        ShiftTab: goUp,
        Tab: goDown,
        k: goUp,
        j: goDown,
        '/': focusSearch,
    };
    let activeIdx = -1;

    document.addEventListener('DOMContentLoaded', () => {
        searchBar = document.querySelector('#search-bar');
        results = document.querySelectorAll('#main>div>div>div>a');
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Shift') {
            shift = true;
        }

        if (e.target.tagName === 'INPUT') return true;
        if (typeof keymap[e.key] === 'function') {
            e.preventDefault();

            keymap[`${shift && e.key == 'Tab' ? 'Shift' : ''}${e.key}`]();
        }
    });

    document.addEventListener('keyup', (e) => {
        if (e.key === 'Shift') {
            shift = false;
        }
    });

    function goUp () {
        if (activeIdx > 0) focusResult(activeIdx - 1);
        else focusSearch();
    }

    function goDown () {
        if (activeIdx < results.length - 1) focusResult(activeIdx + 1);
    }

    function focusResult (idx) {
        activeIdx = idx;
        results[activeIdx].scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
        results[activeIdx].focus();
    }

    function focusSearch () {
        if (window.usingCalculator) {
            // if this function exists, it means the calculator widget has been displayed
            if (usingCalculator()) return;
        }
        activeIdx = -1;
        searchBar.focus();
    }
}());
