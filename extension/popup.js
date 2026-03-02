document.addEventListener('DOMContentLoaded', async () => {
    const summarizeBtn = document.getElementById('summarizeBtn');
    const resultDiv = document.getElementById('result');
    const statusDiv = document.getElementById('status');
    const loaderContainer = document.getElementById('loaderContainer');
    const progressText = document.getElementById('progressText');
    const customPromptArea = document.getElementById('customPrompt');

    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url.includes('youtube.com/watch')) {
        summarizeBtn.disabled = true;
        customPromptArea.disabled = true;
        statusDiv.textContent = "Please navigate to a YouTube video.";
        return;
    }

    statusDiv.textContent = "Ready to create notes!";

    summarizeBtn.addEventListener('click', async () => {
        const promptText = customPromptArea.value.trim() || "Give me a detailed summary of this video with key takeaways.";

        summarizeBtn.disabled = true;
        customPromptArea.disabled = true;
        loaderContainer.style.display = 'flex';
        progressText.textContent = "Extracting and analyzing... (This may take up to a minute)";
        resultDiv.style.display = 'none';

        try {
            const response = await fetch('http://localhost:8000/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: tab.url,
                    prompt: promptText
                })
            });

            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error('API Quota Exceeded. Try again later.');
                }
                throw new Error('Failed to connect to server.');
            }

            const data = await response.json();

            // Render Markdown securely using marked.js
            resultDiv.innerHTML = marked.parse(data.summary);
            resultDiv.style.display = 'block';
            statusDiv.textContent = "Notes generated successfully!";
        } catch (error) {
            statusDiv.textContent = "Error: " + error.message;
        } finally {
            loaderContainer.style.display = 'none';
            summarizeBtn.disabled = false;
            customPromptArea.disabled = false;
            summarizeBtn.textContent = "Regenerate Notes";
        }
    });

    // Make links in result open in new tab
    resultDiv.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') {
            e.preventDefault();
            chrome.tabs.create({ url: e.target.href });
        }
    });
});
