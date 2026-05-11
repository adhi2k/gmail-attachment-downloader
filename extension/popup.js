document.getElementById('downloadForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;
    const extension = document.getElementById('extension').value;

    const button = document.getElementById('downloadBtn');
    const btnText = button.querySelector('.btn-text');
    const loader = document.getElementById('loader');
    const statusBox = document.getElementById('statusBox');
    const statusText = document.getElementById('status');

    // UI Loading state
    button.disabled = true;
    btnText.innerText = 'Processing...';
    loader.classList.remove('hidden');
    statusBox.classList.add('hidden');
    statusBox.classList.remove('error', 'success');

    try {
        const response = await fetch('http://127.0.0.1:5000/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password,
                start_date: start,
                end_date: end,
                extension
            })
        });

        const contentType = response.headers.get("content-type");

        if (response.ok && contentType && contentType.includes("application/zip")) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Trigger download via Chrome API if available, otherwise fallback
            if (typeof chrome !== 'undefined' && chrome.downloads) {
                chrome.downloads.download({
                    url: url,
                    filename: 'attachments.zip',
                    saveAs: true
                }, (downloadId) => {
                    if (chrome.runtime.lastError) {
                        showStatus('Error starting download: ' + chrome.runtime.lastError.message, 'error');
                    } else {
                        showStatus('Downloaded successfully!', 'success');
                    }
                    window.URL.revokeObjectURL(url);
                });
            } else {
                const a = document.createElement('a');
                a.href = url;
                a.download = 'attachments.zip';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                showStatus('Downloaded successfully!', 'success');
            }
        } else {
            const result = await response.json();
            showStatus(result.message || 'An error occurred', 'error');
        }
    } catch (error) {
        showStatus('Connection failed. Make sure the backend server is running.', 'error');
    } finally {
        // Reset UI state
        button.disabled = false;
        btnText.innerText = 'Download Attachments';
        loader.classList.add('hidden');
    }

    function showStatus(message, type) {
        statusText.innerText = message;
        statusBox.className = `status-box ${type}`;
    }
});