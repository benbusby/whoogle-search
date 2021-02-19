(function () {
	let searchBar, results;
	const keymap = {
		ArrowUp: goUp,
		ArrowDown: goDown,
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
		if (e.target.tagName === 'INPUT') return true;
		if (typeof keymap[e.key] === 'function') {
			e.preventDefault();
			keymap[e.key]();
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
		activeIdx = -1;
		searchBar.focus();
	}
}());
