document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start');

    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        if (startButton.style.backgroundColor === 'maroon') {
            startButton.style.backgroundColor = '#6a3acb';
            startButton.style.backgroundImage = "url('static/image/record-start.png')";
            fetch('/stop_recording', { method: "POST" });
        } else {
            startButton.style.backgroundColor = 'maroon';
            startButton.style.backgroundImage = "url('static/image/record-stop.png')";
            fetch('/start_recording', { method: "POST" });
        }
        timeout(startButton);
    });

    function timeout(button) {
        // Set timer to prevent spamming
        setTimeout(() => {
            button.disabled = false;
        }, 1000);
    }
});