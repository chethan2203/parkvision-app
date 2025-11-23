// Update parking statistics every second
function updateStats() {
    fetch('/counts')
        .then(response => response.json())
        .then(data => {
            // Update count displays
            document.getElementById('empty-count').textContent = data.empty;
            document.getElementById('occupied-count').textContent = data.occupied;
            document.getElementById('total-count').textContent = data.total;
            
            // Calculate and update availability
            const availability = data.total > 0 
                ? Math.round((data.empty / data.total) * 100) 
                : 0;
            
            document.getElementById('availability-bar').style.width = availability + '%';
            document.getElementById('availability-text').textContent = availability + '% Available';
            
            // Change color based on availability
            const bar = document.getElementById('availability-bar');
            if (availability > 50) {
                bar.style.background = 'linear-gradient(90deg, #11998e 0%, #38ef7d 100%)';
            } else if (availability > 20) {
                bar.style.background = 'linear-gradient(90deg, #f2994a 0%, #f2c94c 100%)';
            } else {
                bar.style.background = 'linear-gradient(90deg, #eb3349 0%, #f45c43 100%)';
            }
        })
        .catch(error => console.error('Error fetching stats:', error));
}

// Update stats every second
setInterval(updateStats, 1000);

// Initial update
updateStats();

// Handle image upload
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const fpsDisplay = document.getElementById('fps-display');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });

    // Handle file selection
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            uploadImage(file);
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = '#f0f8ff';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.backgroundColor = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = '';
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            uploadImage(file);
        }
    });

    function uploadImage(file) {
        fpsDisplay.textContent = 'Analyzing image...';
        
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the counts in real-time
                updateCounts(data.empty || 0, data.occupied || 0, data.total || 0);
                
                fpsDisplay.textContent = `Detected ${data.total} spaces`;
                
                // Show detection summary
                if (data.total > 0) {
                    const availability = Math.round((data.empty / data.total) * 100);
                    fpsDisplay.textContent = `Found ${data.total} spaces (${availability}% available)`;
                } else {
                    fpsDisplay.textContent = 'No parking spaces detected';
                }
            } else {
                fpsDisplay.textContent = 'Detection failed: ' + (data.error || 'Unknown error');
                updateCounts(0, 0, 0);
            }
        })
        .catch(error => {
            fpsDisplay.textContent = 'Error: ' + error.message;
            updateCounts(0, 0, 0);
        });
    }

    function updateCounts(empty, occupied, total) {
        // Update count displays
        const emptyEl = document.getElementById('empty-count');
        const occupiedEl = document.getElementById('occupied-count');
        const totalEl = document.getElementById('total-count');
        
        if (emptyEl) emptyEl.textContent = empty;
        if (occupiedEl) occupiedEl.textContent = occupied;
        if (totalEl) totalEl.textContent = total;
        
        // Calculate and update availability
        const availability = total > 0 ? Math.round((empty / total) * 100) : 0;
        
        const availabilityBar = document.getElementById('availability-bar');
        const availabilityText = document.getElementById('availability-text');
        
        if (availabilityBar) {
            availabilityBar.style.width = availability + '%';
            
            // Change color based on availability
            if (availability > 70) {
                availabilityBar.style.backgroundColor = '#4CAF50'; // Green
            } else if (availability > 30) {
                availabilityBar.style.backgroundColor = '#FF9800'; // Orange
            } else {
                availabilityBar.style.backgroundColor = '#F44336'; // Red
            }
        }
        
        if (availabilityText) {
            availabilityText.textContent = availability + '% Available';
        }
    }
});