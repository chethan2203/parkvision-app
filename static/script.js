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
