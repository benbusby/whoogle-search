document.addEventListener('DOMContentLoaded', () => {
    const speechToTextBtns = document.querySelectorAll('.speech-to-text-btn');

    if (speechToTextBtns.length === 0) {
        console.warn('Speech-to-text buttons not found.');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Web Speech API is not supported in this browser.');
        speechToTextBtns.forEach(btn => btn.style.display = 'none'); // Hide all buttons if API not supported
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    let activeBtn = null;
    let activeSearchInput = null;
    let activeSearchForm = null;

    speechToTextBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            activeBtn = btn;
            activeSearchForm = btn.closest('form');
            if (activeSearchForm) {
                activeSearchInput = activeSearchForm.querySelector('input[name="q"]');
            }

            if (!activeSearchInput) {
                console.error('Could not find search input associated with the button.');
                return;
            }

            activeBtn.disabled = true;
            activeBtn.textContent = '🔴'; // Indicate listening
            activeSearchInput.placeholder = 'Listening...';
            recognition.start();
        });
    });

    recognition.onresult = (event) => {
        if (!activeSearchInput) return;
        const speechResult = event.results[0][0].transcript;
        activeSearchInput.value = speechResult;
        console.log('Speech result: ' + speechResult);
        console.log('Confidence: ' + event.results[0][0].confidence);
    };

    recognition.onspeechend = () => {
        recognition.stop();
        if (activeBtn) {
            activeBtn.disabled = false;
            activeBtn.textContent = '🎙️'; // Reset button text
        }
        if (activeSearchInput) {
            activeSearchInput.placeholder = 'Whoogle Search';
        }
        if (activeSearchForm) {
            activeSearchForm.submit(); // Automatically submit the form
        }
    };

    recognition.onerror = (event) => {
        if (activeBtn) {
            activeBtn.disabled = false;
            activeBtn.textContent = '🎙️'; // Reset button text
        }
        if (activeSearchInput) {
            activeSearchInput.placeholder = 'Whoogle Search';
        }
        console.error('Speech recognition error: ' + event.error);
        if (event.error === 'no-speech') {
            alert('No speech was detected. Please try again.');
        } else if (event.error === 'not-allowed') {
            alert('Microphone access was denied. Please allow access to use speech-to-text.');
        } else {
            alert('An error occurred during speech recognition: ' + event.error);
        }
    };

    recognition.onnomatch = () => {
        console.log('Speech not recognized.');
        alert('Could not understand speech. Please try again.');
    };
});
